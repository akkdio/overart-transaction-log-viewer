# Useful Commands

## Check Application Status

### Container Status
```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# Check specific container
docker ps | grep transaction-log-viewer
```

### Application Logs
```bash
# Follow logs in real-time
docker logs -f transaction-log-viewer

# View last 100 lines
docker logs --tail 100 transaction-log-viewer

# View logs with timestamps
docker logs -t transaction-log-viewer
```

### Nginx Logs
```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log

# View last 50 lines of access log
sudo tail -n 50 /var/log/nginx/access.log
```

## Restart Application

```bash
# Restart the container
docker restart transaction-log-viewer

# Stop the container
docker stop transaction-log-viewer

# Start the container
docker start transaction-log-viewer
```

## Update Application

```bash
# Run the deployment script (pulls latest image and restarts)
./deploy-app.sh

# Or manually:
docker stop transaction-log-viewer
docker rm transaction-log-viewer
docker pull yourcompany/transaction-log-viewer:latest
docker run -d \
  --name transaction-log-viewer \
  --restart unless-stopped \
  -p 8501:8501 \
  -e S3_BUCKET_NAME=transaction-logs-overart \
  -e AWS_REGION=us-east-1 \
  yourcompany/transaction-log-viewer:latest
```

## Check S3 Access

```bash
# List recent logs
aws s3 ls s3://transaction-logs-overart/logs/ --recursive | tail -20

# List logs for a specific date
aws s3 ls s3://transaction-logs-overart/logs/2024/01/15/ --recursive

# Read a specific log file
aws s3 cp s3://transaction-logs-overart/logs/2024/01/15/transaction_xxx.json - | jq .

# Count total log files
aws s3 ls s3://transaction-logs-overart/logs/ --recursive | wc -l

# Check bucket size
aws s3 ls s3://transaction-logs-overart/logs/ --recursive --summarize | tail -1
```

## System Resources

```bash
# Memory usage
free -h

# Disk usage
df -h

# CPU usage
top

# Or use htop (if installed)
htop

# Check Docker disk usage
docker system df

# Clean up unused Docker resources
docker system prune -a
```

## Nginx Management

```bash
# Check nginx status
sudo systemctl status nginx

# Restart nginx
sudo systemctl restart nginx

# Reload nginx configuration
sudo nginx -s reload

# Test nginx configuration
sudo nginx -t

# View nginx configuration
cat /etc/nginx/sites-available/transaction-log-viewer
```

## Docker Management

```bash
# View Docker images
docker images

# Remove unused images
docker image prune -a

# View Docker system information
docker info

# View container resource usage
docker stats transaction-log-viewer

# Execute command in running container
docker exec -it transaction-log-viewer /bin/bash
```

## Troubleshooting

```bash
# Check if port 8501 is in use
sudo netstat -tulpn | grep 8501

# Check if port 80 is in use
sudo netstat -tulpn | grep 80

# Test Streamlit health endpoint
curl http://localhost:8501/_stcore/health

# Test from outside (replace with your IP)
curl http://52.205.10.200/_stcore/health

# Check IAM role is attached
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# View systemd service status
sudo systemctl status transaction-log-viewer

# View service logs
sudo journalctl -u transaction-log-viewer -f
```

