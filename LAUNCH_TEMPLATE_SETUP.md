# EC2 Launch Template Setup Guide

This guide walks you through creating an EC2 Launch Template for the Transaction Log Viewer application. The template allows you to quickly launch new spot instances with all required configuration.

## Prerequisites

- AWS Console access
- Security group `transaction-log-viewer-sg` created (from Phase 2, Step 4)
- IAM role `overart-TransactionLogReader` created (from Phase 2, Step 3)
- EC2 Key Pair for SSH access
- Elastic IP `52.205.10.200` allocated (from Phase 2, Step 5)

## Step-by-Step Instructions

### 1. Navigate to Launch Templates

1. Log into AWS Console
2. Go to **EC2** → **Launch Templates**
3. Click **Create launch template**

### 2. Basic Configuration

**Template name**: `transaction-log-viewer-template`

**Template description**: 
```
Launch template for Transaction Log Viewer spot instance.
Includes Docker, Nginx, and auto-deployment configuration.
```

**Auto Scaling guidance**: Leave unchecked (we're using spot instances manually)

### 3. AMI Selection

1. Click **Browse more AMIs**
2. Search for: `Ubuntu Server 22.04 LTS`
3. Select: **Ubuntu Server 22.04 LTS** (64-bit x86)
4. Architecture: **64-bit (x86)**

### 4. Instance Type

1. **Instance type**: `t3.small`
   - This is suitable for the Streamlit application
   - Can be changed to `t3a.small` for better spot pricing

### 5. Key Pair

1. **Key pair (login)**: Select your existing EC2 key pair
   - This is required for SSH access
   - If you don't have one, create a new key pair first

### 6. Network Settings

1. **VPC**: Select your default VPC (or preferred VPC)
2. **Subnet**: Select any subnet in your VPC
3. **Auto-assign public IP**: **Enable**
4. **Security groups**: Select `transaction-log-viewer-sg`
   - This security group should allow:
     - Port 80 (HTTP)
     - Port 443 (HTTPS)
     - Port 8501 (Streamlit)
     - Port 22 (SSH) from your IP

### 7. Storage

1. **Volume 1 (Root)**: 
   - **Size**: 20 GB
   - **Volume type**: `gp3`
   - **Delete on termination**: Checked (optional, for cost savings)

### 8. Advanced Details

#### 8.1 IAM Instance Profile

1. **IAM instance profile**: Select `overart-TransactionLogReader`
   - This allows the instance to read from S3 without credentials

#### 8.2 User Data

1. Click **As text**
2. Copy the **entire content** from `ec2-setup.sh` file
3. Paste it into the user data field

**Important**: The user data script will:
- Install Docker and Nginx
- Configure the reverse proxy
- Create the deployment script
- Automatically deploy the application on first boot

#### 8.3 Spot Instance Configuration

1. Scroll to **Purchasing options**
2. Check **Request Spot Instances**
3. **Maximum price**: Leave as default (on-demand price)
   - Or set a custom price if you want to limit costs
4. **Spot request type**: `one-time`
5. **Interruption behavior**: `terminate`

#### 8.4 Additional Settings

- **Enable detailed CloudWatch monitoring**: Optional (adds cost)
- **Termination protection**: Unchecked (spot instances can't use this)
- **Shutdown behavior**: `terminate`

### 9. Tags (Optional but Recommended)

Add tags for easier identification:

| Key | Value |
|-----|-------|
| `Name` | `transaction-log-viewer` |
| `Application` | `transaction-log-viewer` |
| `Environment` | `production` |
| `ManagedBy` | `launch-template` |

### 10. Create Template

1. Review all settings
2. Click **Create launch template**

## Using the Launch Template

### Launch New Instance

1. Go to **EC2** → **Launch Templates**
2. Select `transaction-log-viewer-template`
3. Click **Actions** → **Launch instance from template**
4. **Number of instances**: 1
5. **Purchasing option**: Check **Request Spot Instances**
6. Click **Launch instance**

### Associate Elastic IP

After the instance is running:

1. Go to **EC2** → **Elastic IPs**
2. Select Elastic IP `52.205.10.200`
3. Click **Actions** → **Associate Elastic IP address**
4. Select the new instance
5. Click **Associate**

### Verify Deployment

1. Wait 5-7 minutes for setup script to complete
2. Check application: `http://52.205.10.200`
3. Or via domain: `http://transaction-logs.overart.us`

## Template Configuration Summary

| Setting | Value |
|---------|-------|
| **Template Name** | `transaction-log-viewer-template` |
| **AMI** | Ubuntu Server 22.04 LTS |
| **Instance Type** | t3.small (spot) |
| **Key Pair** | [Your key pair] |
| **Security Group** | `transaction-log-viewer-sg` |
| **IAM Role** | `overart-TransactionLogReader` |
| **Storage** | 20 GB gp3 |
| **User Data** | Content from `ec2-setup.sh` |
| **Spot Instance** | Enabled |
| **Public IP** | Auto-assign enabled |

## Troubleshooting

### Instance Fails to Launch

- Check spot instance capacity in your region
- Try a different instance type (t3a.small, t3.medium)
- Verify security group exists
- Verify IAM role exists

### Application Not Deploying

- Check CloudWatch logs: EC2 → Instances → Select instance → Actions → Monitor and troubleshoot → Get system log
- SSH into instance and check: `sudo journalctl -u transaction-log-viewer -f`
- Verify Docker is running: `sudo systemctl status docker`
- Manually run deployment: `./deploy-app.sh`

### Can't Access Application

- Verify Elastic IP is associated
- Check security group allows port 80
- Verify Nginx is running: `sudo systemctl status nginx`
- Check container status: `docker ps`

## Cost Optimization

- **Spot Instances**: Use spot pricing (60-90% savings)
- **Instance Type**: t3.small is sufficient, can use t3.micro for lower cost (may be slower)
- **Storage**: 20 GB is minimum, increase if needed
- **Monitoring**: Disable detailed monitoring to save costs

## Next Steps

After creating the template:

1. Test launch an instance
2. Verify auto-deployment works
3. Associate Elastic IP
4. Test application access
5. Document your key pair name for future reference

