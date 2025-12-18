import streamlit as st
import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import sys
from pathlib import Path

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# Configuration
USE_LOCAL_DATA = os.getenv('USE_LOCAL_DATA', 'false').lower() == 'true'
LOCAL_DATA_PATH = os.getenv('LOCAL_DATA_PATH', 'local_data')
S3_BUCKET = os.getenv('S3_BUCKET_NAME', 'transaction-logs-overart')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize S3 client (only if not using local data)
if not USE_LOCAL_DATA:
    s3 = boto3.client('s3', region_name=AWS_REGION)

st.set_page_config(
    page_title="Transaction Log Viewer",
    page_icon="📊",
    layout="wide"
)

def convert_raw_transactions():
    """
    Convert raw transaction data from .txt file to S3 format.
    Called automatically when refreshing data.
    """
    try:
        from parse_transaction_text import parse_multiple_transactions
    except ImportError:
        st.warning("Parser module not found. Raw data conversion disabled.")
        return 0
    
    raw_txt_file = Path(LOCAL_DATA_PATH) / "raw_transactions.txt"
    output_base = Path(LOCAL_DATA_PATH) / "logs"
    
    if not raw_txt_file.exists():
        return 0  # No raw file to process
    
    # Read raw data
    with open(raw_txt_file, 'r') as f:
        content = f.read().strip()
    
    if not content:
        return 0  # Empty file
    
    # Check if it's text format (contains Transaction[)
    if 'Transaction[' not in content:
        return 0  # Not text format, skip
    
    # Parse transactions
    transactions = parse_multiple_transactions(content)
    
    if not transactions:
        return 0
    
    converted = 0
    for transaction in transactions:
        try:
            # Ensure required fields
            if 'timestamp' not in transaction:
                continue
            if 'transaction_id' not in transaction:
                continue
            
            # Parse timestamp
            timestamp_str = transaction['timestamp']
            try:
                # Try different formats
                for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                    try:
                        dt = datetime.strptime(timestamp_str.replace('+00:00', '').replace('Z', ''), fmt.replace('Z', ''))
                        break
                    except ValueError:
                        continue
                else:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                continue
            
            # Create directory structure
            date_dir = output_base / dt.strftime("%Y") / dt.strftime("%m") / dt.strftime("%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Sanitize ID for filename
            transaction_id = transaction['transaction_id']
            safe_id = "".join(c if c.isalnum() or c in '-_' else '_' for c in str(transaction_id))
            filename = f"transaction_{safe_id}.json"
            filepath = date_dir / filename
            
            # Save transaction
            with open(filepath, 'w') as f:
                json.dump(transaction, f, indent=2)
            
            converted += 1
        except Exception as e:
            continue
    
    return converted


st.title("📊 Transaction Log Viewer")
if USE_LOCAL_DATA:
    st.info("🔧 Running in LOCAL MODE - Using local data files")
st.markdown("---")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_logs_from_local(date_filter=None):
    """Load transaction logs from local file system"""
    logs = []
    
    try:
        base_path = Path(LOCAL_DATA_PATH) / "logs"
        
        if not base_path.exists():
            st.error(f"Local data directory not found: {base_path}")
            return []
        
        # If date filter provided, use it for path
        if date_filter:
            date_path = base_path / date_filter.strftime('%Y/%m/%d')
            search_paths = [date_path] if date_path.exists() else []
        else:
            # Get logs from last 7 days
            search_paths = []
            for i in range(7):
                date = datetime.now() - timedelta(days=i)
                date_path = base_path / date.strftime('%Y/%m/%d')
                if date_path.exists():
                    search_paths.append(date_path)
        
        # Walk through directories and load JSON files
        for search_path in search_paths:
            if search_path.exists():
                for json_file in search_path.glob('*.json'):
                    try:
                        with open(json_file, 'r') as f:
                            log_entry = json.load(f)
                            logs.append(log_entry)
                    except (json.JSONDecodeError, IOError) as e:
                        # Skip invalid files
                        continue
        
        return logs
    
    except Exception as e:
        st.error(f"Error loading logs from local files: {str(e)}")
        return []

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_logs_from_s3(date_filter=None):
    """Load transaction logs from S3
    
    Supports both:
    - .txt files: Raw transaction text (parsed on-the-fly)
    - .json files: Pre-parsed transaction data (backward compatibility)
    """
    logs = []
    
    try:
        # Import parser for raw text files
        from parse_transaction_text import parse_transaction_text
        
        # If date filter provided, use it for prefix
        if date_filter:
            prefix = f"logs/{date_filter.strftime('%Y/%m/%d')}/"
        else:
            # Get logs from last 7 days
            prefix = "logs/"
        
        # List objects in S3
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
        
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                # Accept both .txt (raw text) and .json (pre-parsed) files
                if not (obj['Key'].endswith('.json') or obj['Key'].endswith('.txt')):
                    continue
                
                try:
                    # Get object content
                    response = s3.get_object(Bucket=S3_BUCKET, Key=obj['Key'])
                    content = response['Body'].read().decode('utf-8')
                    
                    if obj['Key'].endswith('.txt'):
                        # Parse raw text file on-the-fly
                        parsed = parse_transaction_text(content.strip())
                        if parsed:
                            logs.append(parsed)
                        else:
                            # Log parsing failure but continue
                            st.warning(f"Failed to parse transaction from {obj['Key']}")
                    else:
                        # Load JSON file (existing behavior for backward compatibility)
                        log_entry = json.loads(content)
                        logs.append(log_entry)
                        
                except json.JSONDecodeError as e:
                    # Invalid JSON file - skip it
                    st.warning(f"Invalid JSON in {obj['Key']}: {str(e)}")
                    continue
                except Exception as e:
                    # Other errors (parsing, network, etc.) - skip this file
                    st.warning(f"Error processing {obj['Key']}: {str(e)}")
                    continue
        
        return logs
    
    except Exception as e:
        st.error(f"Error loading logs from S3: {str(e)}")
        return []

# Sidebar filters
st.sidebar.header("Filters")

# Date filter
date_option = st.sidebar.radio(
    "Select Date Range:",
    ["Today", "Yesterday", "Last 7 Days", "Custom Date"]
)

date_filter = None
if date_option == "Today":
    date_filter = datetime.now()
elif date_option == "Yesterday":
    date_filter = datetime.now() - timedelta(days=1)
elif date_option == "Custom Date":
    date_filter = st.sidebar.date_input("Select Date")
    if isinstance(date_filter, datetime.date):
        date_filter = datetime.combine(date_filter, datetime.min.time())

# Refresh button - at top for visibility
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh & Convert Data"):
    # Convert raw transactions first (if local mode)
    if USE_LOCAL_DATA:
        with st.spinner("Converting raw transactions..."):
            converted = convert_raw_transactions()
            if converted > 0:
                st.sidebar.success(f"✓ Converted {converted} transaction(s)")
    
    # Clear cache and rerun
    st.cache_data.clear()
    st.rerun()

# Show raw file status in local mode
if USE_LOCAL_DATA:
    raw_txt_file = Path(LOCAL_DATA_PATH) / "raw_transactions.txt"
    if raw_txt_file.exists():
        with open(raw_txt_file, 'r') as f:
            content = f.read()
        tx_count = content.count('Transaction[')
        st.sidebar.info(f"📄 raw_transactions.txt: {tx_count} transaction(s) found")
    else:
        st.sidebar.warning("📄 No raw_transactions.txt file found")

# Load logs
with st.spinner("Loading transaction logs..."):
    if USE_LOCAL_DATA:
        logs = load_logs_from_local(date_filter if date_option != "Last 7 Days" else None)
    else:
        logs = load_logs_from_s3(date_filter if date_option != "Last 7 Days" else None)

if not logs:
    st.warning("No transaction logs found for the selected date range.")
    st.info("💡 Paste transactions into `local_data/raw_transactions.txt` and click **Refresh & Convert Data**")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(logs)

# Transaction ID search
search_id = st.sidebar.text_input("🔍 Search Transaction ID:")
if search_id:
    df = df[df['transaction_id'].str.contains(search_id, case=False, na=False)]

# Status filter
if 'status' in df.columns:
    statuses = ['All'] + sorted(df['status'].unique().tolist())
    status_filter = st.sidebar.selectbox("Filter by Status:", statuses)
    if status_filter != 'All':
        df = df[df['status'] == status_filter]

# Display metrics
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Transactions", len(df))

with col2:
    if 'status' in df.columns:
        success_count = len(df[df['status'] == 'success'])
        st.metric("Successful", success_count)

with col3:
    if 'status' in df.columns:
        pending_count = len(df[df['status'] == 'pending'])
        st.metric("Pending", pending_count)

with col4:
    if 'status' in df.columns:
        failed_count = len(df[df['status'] == 'failed'])
        st.metric("Failed", failed_count)

with col5:
    if 'amount' in df.columns:
        total_amount = df['amount'].sum()
        st.metric("Total Amount", f"${total_amount:,.2f}")

st.markdown("---")

# Display transaction table
st.subheader("Transaction Details")

# Select columns to display
display_columns = ['timestamp', 'transaction_id', 'status']
if 'amount' in df.columns:
    display_columns.append('amount')

# Format and display
st.dataframe(
    df[display_columns].sort_values('timestamp', ascending=False),
    use_container_width=True,
    height=400
)

# Detailed view for selected transaction
st.markdown("---")
st.subheader("Detailed Transaction View")

selected_id = st.selectbox(
    "Select Transaction ID for Details:",
    options=df['transaction_id'].unique()
)

if selected_id:
    selected_tx = df[df['transaction_id'] == selected_id].iloc[0].to_dict()
    
    # Check if we have the three representations
    has_representations = all(k in selected_tx for k in ['raw_text', 'json_full', 'json_compact'])
    
    if has_representations:
        # Tabbed view with three representations
        tab_raw, tab_full, tab_compact = st.tabs(["📝 Raw Text", "📋 JSON (Full)", "📦 JSON (Compact)"])
        
        with tab_raw:
            st.caption("Original transaction text as received")
            st.code(selected_tx.get('raw_text', 'No raw text available'), language=None)
        
        with tab_full:
            st.caption("All fields including null values")
            json_full = selected_tx.get('json_full', {})
            st.json(json_full)
        
        with tab_compact:
            st.caption("Filtered view - null values removed")
            json_compact = selected_tx.get('json_compact', {})
            st.json(json_compact)
    else:
        # Fallback for older data format without representations
        col1, col2 = st.columns(2)
        
        with col1:
            st.json(selected_tx)
        
        with col2:
            st.write("**Transaction Details:**")
            for key, value in selected_tx.items():
                if key not in ['raw_text', 'json_full', 'json_compact']:
                    st.write(f"**{key}:** {value}")
