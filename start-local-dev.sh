#!/bin/bash
set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Transaction Log Viewer - Local Dev${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Error: python3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${BLUE}Checking dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if any raw data file exists (supports both .txt and .json)
if [ -f "local_data/raw_transactions.txt" ]; then
    echo -e "${GREEN}Found raw_transactions.txt (text format)${NC}"
elif [ -f "local_data/raw_transactions.json" ]; then
    echo -e "${GREEN}Found raw_transactions.json (JSON format)${NC}"
else
    echo -e "${YELLOW}No raw transaction data found.${NC}"
    echo -e "${YELLOW}Creating example files...${NC}"
    # Create JSON example
    cp local_data/raw_transactions.example.json local_data/raw_transactions.json 2>/dev/null || true
    echo ""
    echo -e "${YELLOW}Please add your transaction data to one of:${NC}"
    echo -e "${YELLOW}  - local_data/raw_transactions.txt (for text format - Java/Kotlin object strings)${NC}"
    echo -e "${YELLOW}  - local_data/raw_transactions.json (for JSON format)${NC}"
    echo ""
    echo -e "${YELLOW}See local_data/raw_transactions.example.* for format examples.${NC}"
fi

# Check if converted data exists
if [ ! -d "local_data/logs" ] || [ -z "$(ls -A local_data/logs 2>/dev/null)" ]; then
    echo -e "${YELLOW}No converted data found. Running converter...${NC}"
    python scripts/convert_raw_to_local.py || {
        echo -e "${YELLOW}Converter had issues. Continuing anyway...${NC}"
    }
else
    echo -e "${GREEN}Converted data found.${NC}"
fi

# Ask user how to run
echo ""
echo -e "${BLUE}How would you like to run the app?${NC}"
echo "1) Streamlit directly (fastest, recommended for dev)"
echo "2) Docker container (matches production)"
read -p "Enter choice [1]: " choice
choice=${choice:-1}

if [ "$choice" = "2" ]; then
    # Docker mode
    echo ""
    echo -e "${BLUE}Building Docker image...${NC}"
    docker build -t transaction-log-viewer:local .
    
    echo ""
    echo -e "${BLUE}Starting Docker container...${NC}"
    echo -e "${GREEN}App will be available at: http://localhost:8501${NC}"
    echo ""
    
    # Stop existing container if running
    docker stop transaction-log-viewer-local 2>/dev/null || true
    docker rm transaction-log-viewer-local 2>/dev/null || true
    
    # Run container with local data mounted
    docker run -d \
        --name transaction-log-viewer-local \
        -p 8501:8501 \
        -e USE_LOCAL_DATA=true \
        -e LOCAL_DATA_PATH=/app/local_data \
        -v "$(pwd)/local_data:/app/local_data" \
        transaction-log-viewer:local
    
    echo ""
    echo -e "${GREEN}Container started!${NC}"
    echo -e "${BLUE}View logs: docker logs -f transaction-log-viewer-local${NC}"
    echo -e "${BLUE}Stop container: docker stop transaction-log-viewer-local${NC}"
    echo ""
    docker logs -f transaction-log-viewer-local
else
    # Direct Streamlit mode
    echo ""
    echo -e "${BLUE}Starting Streamlit app...${NC}"
    echo -e "${GREEN}App will be available at: http://localhost:8501${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
    # Set environment variables and run
    export USE_LOCAL_DATA=true
    export LOCAL_DATA_PATH=local_data
    streamlit run app.py
fi

