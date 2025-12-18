#!/bin/bash
set -e  # Exit on any error

echo "=========================================="
echo "Transaction Log Viewer - EC2 Setup Script"
echo "=========================================="

# Configuration
DOMAIN="transaction-viewer-log.overart.us"
EMAIL="akkdio@simplytrue.org  # UPDATE THIS for Let's Encrypt notifications

# Update system
echo "Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Install nginx (reverse proxy)
echo "Installing Nginx..."
sudo apt-get install -y nginx

# Install Certbot for Let's Encrypt
echo "Installing Certbot..."
sudo apt-get install -y certbot python3-certbot-nginx

# Configure Nginx (initial HTTP-only config for Let's Encrypt verification)
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/transaction-log-viewer > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/transaction-log-viewer /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Create deployment script
echo "Creating deployment script..."
sudo tee /home/ubuntu/deploy-app.sh > /dev/null <<'DEPLOY_SCRIPT'
#!/bin/bash
set -e

# Configuration - UPDATE THESE VALUES
DOCKER_IMAGE="radialsimplytrue/transaction-log-viewer:latest"
CONTAINER_NAME="transaction-log-viewer"
S3_BUCKET_NAME="transaction-logs-overart"
AWS_REGION="us-east-1"

echo "Stopping existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "Pulling latest image..."
docker pull $DOCKER_IMAGE

echo "Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p 8501:8501 \
  -e S3_BUCKET_NAME=$S3_BUCKET_NAME \
  -e AWS_REGION=$AWS_REGION \
  $DOCKER_IMAGE

echo "Waiting for container to be healthy..."
sleep 10

echo "Checking container status..."
docker ps | grep $CONTAINER_NAME

echo "Deployment complete!"
DEPLOY_SCRIPT

# Make deployment script executable
sudo chmod +x /home/ubuntu/deploy-app.sh

# Create systemd service for auto-restart
echo "Creating systemd service..."
sudo tee /etc/systemd/system/transaction-log-viewer.service > /dev/null <<'EOF'
[Unit]
Description=Transaction Log Viewer
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/home/ubuntu/deploy-app.sh
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable transaction-log-viewer.service

# Install AWS CLI (for future management)
echo "Installing AWS CLI..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt-get install -y unzip
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Wait for Docker to be fully ready
echo "Waiting for Docker to be ready..."
sleep 5
sudo systemctl status docker --no-pager || true

# Automatically deploy the application
echo "=========================================="
echo "Deploying application..."
echo "=========================================="

# Use sg to run deploy script with docker group active (no logout needed)
sudo -u ubuntu sg docker -c "/home/ubuntu/deploy-app.sh" || {
    echo "Warning: Initial deployment failed, but setup is complete."
    echo "You can manually run: ./deploy-app.sh"
    echo "Or the application will auto-deploy on next reboot via systemd service."
}

# Wait for application to start before obtaining SSL certificate
echo "Waiting for application to start..."
sleep 15

# Obtain SSL certificate with Let's Encrypt
echo "=========================================="
echo "Obtaining SSL Certificate..."
echo "=========================================="
echo "IMPORTANT: Ensure $DOMAIN points to this server's IP before continuing!"
echo "DNS propagation may take a few minutes..."
echo ""

# Check if DNS is properly configured
echo "Checking DNS resolution for $DOMAIN..."
if host $DOMAIN > /dev/null 2>&1; then
    RESOLVED_IP=$(host $DOMAIN | grep "has address" | awk '{print $4}' | head -n1)
    echo "Domain resolves to: $RESOLVED_IP"
    
    # Attempt to get SSL certificate
    sudo certbot --nginx \
        -d $DOMAIN \
        --non-interactive \
        --agree-tos \
        --email $EMAIL \
        --redirect \
        --hsts \
        --staple-ocsp || {
        echo "Warning: SSL certificate installation failed."
        echo "This is usually because:"
        echo "1. DNS is not properly configured (domain must point to this IP)"
        echo "2. Port 80/443 is not open in security group"
        echo ""
        echo "You can manually obtain the certificate later by running:"
        echo "sudo certbot --nginx -d $DOMAIN"
    }
else
    echo "Warning: Domain $DOMAIN does not resolve to an IP address yet."
    echo "Please configure your DNS A record to point to this server's IP."
    echo "After DNS is configured, run: sudo certbot --nginx -d $DOMAIN"
fi

# Set up automatic certificate renewal
echo "Setting up automatic SSL certificate renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Create a renewal hook to reload nginx
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null <<'EOF'
#!/bin/bash
systemctl reload nginx
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo "Application URL: https://$DOMAIN"
echo ""
echo "Next steps if SSL setup failed:"
echo "1. Ensure DNS A record points $DOMAIN to this server's IP"
echo "2. Ensure security group allows ports 80 and 443"
echo "3. Run: sudo certbot --nginx -d $DOMAIN"
echo ""
echo "SSL certificates will auto-renew via certbot.timer"
echo "=========================================="