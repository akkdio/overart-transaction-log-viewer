# Spot Instance Recovery Guide

When the spot instance is terminated, follow these steps:

## 1. Launch New Instance from Template

1. Go to EC2 → Launch Templates
2. Select "transaction-log-viewer-template"
3. Click "Actions" → "Launch instance from template"
4. Check "Request Spot Instances"
5. Click "Launch instance"

## 2. Associate Elastic IP

1. Go to EC2 → Elastic IPs
2. Select your Elastic IP (52.205.10.200)
3. Click "Actions" → "Associate Elastic IP address"
4. Select the new instance
5. Click "Associate"

## 3. Wait for Setup and Auto-Deployment

Wait approximately 5-7 minutes for:
- Setup script to complete (Docker, Nginx installation)
- Application to automatically deploy from Docker Hub

The setup script automatically deploys the application, so no manual deployment is needed.

## 4. Verify Deployment

1. Check container status:
   ```bash
   docker ps
   ```

2. Check container logs:
   ```bash
   docker logs transaction-log-viewer
   ```

3. Test the application:
   - Open browser: `http://52.205.10.200`
   - Or via domain: `http://transaction-logs.overart.us`

## Total Recovery Time

Approximately 5-7 minutes from instance launch to fully operational.

**Note**: The application automatically deploys during instance setup. No manual SSH or deployment steps are required.

## Troubleshooting

If the application doesn't appear after 7 minutes:

1. **SSH into instance** (optional, for debugging):
   ```bash
   ssh -i your-key.pem ubuntu@52.205.10.200
   ```

2. **Check container status**:
   ```bash
   docker ps
   ```

3. **Check deployment logs**:
   ```bash
   sudo journalctl -u transaction-log-viewer -f
   ```

4. **Manually trigger deployment** (if needed):
   ```bash
   ./deploy-app.sh
   ```

## Alternative: Manual Setup

If the launch template is not available, you can manually launch an instance:

1. Launch EC2 instance with:
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.small (spot)
   - Security group: transaction-log-viewer-sg
   - IAM role: overart-TransactionLogReader
   - User data: Copy content from `ec2-setup.sh`

2. Associate Elastic IP (step 2 above)

3. Wait 5-7 minutes for auto-deployment

4. Verify deployment (step 4 above)

