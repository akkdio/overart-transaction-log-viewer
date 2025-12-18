# Transaction Log Viewer

A Streamlit-based dashboard for viewing transaction logs stored in AWS S3. The application is containerized with Docker and deployed on an EC2 Spot instance, accessible via `transaction-logs.overart.us`.

## Architecture

```
S3 Bucket (transaction-logs-overart)
    ↓
Streamlit App (reads logs)
    ↓
Docker Container
    ↓
EC2 Spot Instance (52.205.10.200)
    ↓
Nginx Reverse Proxy
    ↓
transaction-logs.overart.us
```

## Features

- **Date Filtering**: View logs by Today, Yesterday, Last 7 Days, or Custom Date
- **Search**: Search transactions by Transaction ID
- **Status Filtering**: Filter by transaction status (success, failed, etc.)
- **Metrics Dashboard**: View total transactions, success/failed counts, and total amount
- **Detailed View**: Inspect individual transaction details
- **Auto-refresh**: Refresh data with a single click

## Prerequisites

- Python 3.11+
- Docker (for containerization)
- AWS Account with (only if using S3 mode):
  - S3 bucket: `transaction-logs-overart`
  - IAM role with S3 read permissions
  - EC2 instance with IAM role attached

**Note**: Local development mode doesn't require AWS credentials. See [Local Development Setup](#local-development-setup) for details.

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd transaction-log-viewer
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Run Locally

#### Option A: Using S3 (Requires AWS Credentials)

```bash
streamlit run app.py
```

Visit `http://localhost:8501` to see the dashboard.

#### Option B: Using Local Data (No AWS Required)

**Quick Start (Recommended)**:
```bash
./start-local-dev.sh
```

This script will:
- Set up virtual environment (if needed)
- Install dependencies
- Convert raw data (if needed)
- Give you option to run via Streamlit or Docker
- Start the app automatically

**Manual Steps**:

1. **Paste your raw transaction data** into one of:
   - `local_data/raw_transactions.txt` - **Text format** (Java/Kotlin object strings from logs)
   - `local_data/raw_transactions.json` - **JSON format** (standard JSON array)
   
   See `local_data/raw_transactions.example.*` for format examples.

2. **Convert raw data to S3 format**:
   ```bash
   python scripts/convert_raw_to_local.py
   ```
   The converter auto-detects the format and creates files in `local_data/logs/YYYY/MM/DD/`

3. **Run app in local mode**:
   ```bash
   USE_LOCAL_DATA=true streamlit run app.py
   ```
   
   Or set in `.env` file:
   ```bash
   USE_LOCAL_DATA=true
   LOCAL_DATA_PATH=local_data
   ```

4. Visit `http://localhost:8501` to see the dashboard with local data.

**Note**: The app will show "🔧 Running in LOCAL MODE" when using local data.

## Docker Setup

### Build Docker Image

```bash
docker build -t transaction-log-viewer:latest .
```

### Run Docker Container

```bash
docker run -p 8501:8501 \
  -e S3_BUCKET_NAME=transaction-logs-overart \
  -e AWS_REGION=us-east-1 \
  transaction-log-viewer:latest
```

## S3 Log Structure

The application expects logs to be stored in S3 with the following structure:

```
s3://transaction-logs-overart/
└── logs/
    └── YYYY/
        └── MM/
            └── DD/
                ├── transaction_{id}.txt  (raw text - recommended)
                └── transaction_{id}.json  (pre-parsed - backward compatibility)
```

### Supported Formats

**Option 1: Raw Text Files (`.txt`) - Recommended for New Integrations**

Upload raw transaction text exactly as received. The viewer automatically parses it and generates all representations.

- **File**: `transaction_{id}.txt`
- **Content**: Raw `Transaction[...]` text string
- **Example**: See `local_data/raw_transactions.example.txt`

**Option 2: Pre-parsed JSON Files (`.json`) - Backward Compatibility**

Pre-parsed JSON files with all three representations (for existing deployments).

- **File**: `transaction_{id}.json`
- **Content**: JSON object with `raw_text`, `json_full`, `json_compact`
- **Example**: See `local_data/logs/` for structure

**Note**: Both formats work simultaneously. New uploads should use `.txt` format for simplicity.

## Deployment

### Automated Deployment Pipeline

The deployment process is fully automated:

1. **Code Push** → GitHub Actions builds Docker image
2. **Image Push** → Pushed to Docker Hub
3. **Auto-Deploy** → GitHub Actions SSHs to EC2 and deploys automatically
4. **New Instances** → Auto-deploy on first boot via setup script

### Initial EC2 Setup

#### Option 1: Using Launch Template (Recommended)

1. Create launch template following [LAUNCH_TEMPLATE_SETUP.md](docs/LAUNCH_TEMPLATE_SETUP.md)
2. Launch instance from template
3. Associate Elastic IP: `52.205.10.200`
4. Wait 5-7 minutes for automatic deployment

#### Option 2: Manual Launch

1. Launch EC2 instance with:
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.small (spot)
   - Security group: `transaction-log-viewer-sg`
   - IAM role: `overart-TransactionLogReader`
   - User data: Content from `ec2-setup.sh`

2. Associate Elastic IP: `52.205.10.200`

3. Wait 5-7 minutes - application auto-deploys during setup

### CI/CD Pipeline

The GitHub Actions workflow:
1. Builds Docker image on push to `main` branch
2. Pushes image to Docker Hub
3. **Automatically deploys to EC2** via SSH

**Required GitHub Secrets:**
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token
- `EC2_ELASTIC_IP`: `52.205.10.200` (or hardcode in workflow)
- `EC2_SSH_PRIVATE_KEY`: Private key content for EC2 SSH access
- `S3_BUCKET_NAME`: `transaction-logs-overart` (optional)
- `AWS_REGION`: `us-east-1` (optional)

## Configuration

### Environment Variables

**S3 Mode (default)**:
- `S3_BUCKET_NAME`: S3 bucket name (default: `transaction-logs-overart`)
- `AWS_REGION`: AWS region (default: `us-east-1`)

**Local Development Mode**:
- `USE_LOCAL_DATA`: Set to `true` to use local files instead of S3 (default: `false`)
- `LOCAL_DATA_PATH`: Path to local data directory (default: `local_data`)

### Docker Hub Configuration

Update the Docker Hub username in:
- `.github/workflows/deploy.yml` (uses secret)
- `ec2-setup.sh` → `deploy-app.sh` script (DOCKER_IMAGE variable)

## DNS Configuration

Configure DNS A record:
- **Name**: `transaction-logs`
- **Type**: A
- **Value**: `52.205.10.200`
- **TTL**: 300

## Monitoring & Maintenance

See [COMMANDS.md](docs/COMMANDS.md) for useful commands for:
- Checking application status
- Viewing logs
- Restarting services
- Monitoring system resources

## Spot Instance Recovery

If the spot instance is terminated, follow the recovery guide in [RECOVERY.md](docs/RECOVERY.md).

## Troubleshooting

### Dashboard shows "No logs found"
- Verify S3 bucket has logs: `aws s3 ls s3://transaction-logs-overart/logs/`
- Check IAM role is attached to EC2 instance
- Verify container logs: `docker logs transaction-log-viewer`

### Can't access via domain
- Check DNS resolution: `nslookup transaction-logs.overart.us`
- Verify Elastic IP is associated
- Check security group allows port 80
- Check nginx status: `sudo systemctl status nginx`

### Container not starting
- Check Docker logs: `docker logs transaction-log-viewer`
- Verify image pulled: `docker images | grep transaction-log-viewer`
- Check environment variables in deploy script

### GitHub Action fails
- Verify secrets are set correctly in GitHub repository settings
- Check Docker Hub credentials
- Verify `EC2_SSH_PRIVATE_KEY` secret contains the full private key (including `-----BEGIN` and `-----END` lines)
- Check that Elastic IP is associated to a running instance
- Review workflow logs in GitHub Actions tab

### Deployment fails on new instance
- Check CloudWatch logs: EC2 → Instances → Select instance → Actions → Monitor and troubleshoot → Get system log
- SSH into instance and check: `sudo journalctl -u transaction-log-viewer -f`
- Verify Docker is running: `sudo systemctl status docker`
- Manually run deployment: `./deploy-app.sh`

### Local development issues
- **No data showing**: Run `python scripts/convert_raw_to_local.py` to convert raw data
- **Converter script fails**: Check that `local_data/raw_transactions.json` exists and contains valid JSON
- **Wrong date filtering**: Verify converted files are in `local_data/logs/YYYY/MM/DD/` structure
- **App not using local data**: Ensure `USE_LOCAL_DATA=true` is set in environment or `.env` file

## Security Best Practices

1. **S3 Bucket**: Keep bucket private, use IAM roles (not access keys)
2. **EC2 Instance**: Restrict SSH access to your IP only
3. **Docker Hub**: Use private repositories for internal tools
4. **Secrets**: Never commit `.env` files, use GitHub Secrets for CI/CD

## Cost Estimates

- **EC2 t3.small Spot**: ~$5-7/month
- **Elastic IP**: $0 (when associated)
- **S3 Storage**: ~$0.023/GB/month
- **Data Transfer**: Free within same region
- **Total**: ~$10-15/month

## Project Structure

```
transaction-log-viewer/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── Dockerfile                      # Docker container definition
├── .dockerignore                   # Docker build exclusions
├── .gitignore                      # Git exclusions
├── ec2-setup.sh                   # EC2 instance setup script
├── start-local-dev.sh             # Local development startup script
├── README.md                       # This file
├── docs/                           # Documentation (not tracked in git)
│   ├── RECOVERY.md                 # Spot instance recovery guide
│   ├── COMMANDS.md                 # Useful commands reference
│   ├── LAUNCH_TEMPLATE_SETUP.md   # EC2 launch template setup guide
│   └── BACKEND_INTEGRATION.md      # Backend integration guide
├── local_data/                     # Local development data
│   ├── raw_transactions.txt       # Paste text-format data here
│   ├── raw_transactions.json      # Or paste JSON-format data here
│   ├── raw_transactions.example.txt   # Text format example
│   ├── raw_transactions.example.json  # JSON format example
│   └── logs/                       # Converted transaction files
├── scripts/
│   ├── convert_raw_to_local.py    # Convert raw data to S3 format
│   └── parse_transaction_text.py  # Text format parser module
└── .github/
    └── workflows/
        └── deploy.yml              # CI/CD pipeline
```

## License

Internal use only.

