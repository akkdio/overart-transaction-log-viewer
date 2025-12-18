#!/usr/bin/env python3
"""
Convert raw transaction data to S3 format for local development.

This script reads raw transaction data from:
- local_data/raw_transactions.json (JSON format)
- local_data/raw_transactions.txt (Text format - Java/Kotlin object strings)

And converts it to the S3 log format, saving files in local_data/logs/YYYY/MM/DD/
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Import the text parser
from parse_transaction_text import parse_transaction_text, parse_multiple_transactions

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_JSON_FILE = PROJECT_ROOT / "local_data" / "raw_transactions.json"
RAW_TEXT_FILE = PROJECT_ROOT / "local_data" / "raw_transactions.txt"
OUTPUT_BASE = PROJECT_ROOT / "local_data" / "logs"


def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object."""
    # Try different timestamp formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    # If all formats fail, try ISO format parser
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except:
        raise ValueError(f"Unable to parse timestamp: {timestamp_str}")


def extract_transaction_id(transaction):
    """Extract transaction ID from transaction object."""
    # Try different possible field names
    for field in ['transaction_id', 'id', 'transactionId', 'txn_id']:
        if field in transaction:
            return str(transaction[field])
    
    # If no ID found, generate one from timestamp
    timestamp = transaction.get('timestamp', '')
    return f"TXN-{hash(timestamp) % 100000:05d}"


def ensure_required_fields(transaction):
    """Ensure transaction has all required fields."""
    # Ensure timestamp exists
    if 'timestamp' not in transaction:
        raise ValueError("Transaction missing required 'timestamp' field")
    
    # Ensure transaction_id exists
    if 'transaction_id' not in transaction:
        transaction['transaction_id'] = extract_transaction_id(transaction)
    
    # Ensure status exists (default to 'unknown' if not present)
    if 'status' not in transaction:
        transaction['status'] = 'unknown'
    
    return transaction


def convert_transaction(transaction, output_base):
    """Convert a single transaction to S3 format and save it."""
    # Ensure required fields
    transaction = ensure_required_fields(transaction)
    
    # Parse timestamp
    timestamp_str = transaction['timestamp']
    try:
        dt = parse_timestamp(timestamp_str)
    except ValueError as e:
        print(f"Warning: {e}, skipping transaction")
        return None
    
    # Create directory structure: logs/YYYY/MM/DD/
    date_dir = output_base / dt.strftime("%Y") / dt.strftime("%m") / dt.strftime("%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # Get transaction ID
    transaction_id = transaction['transaction_id']
    
    # Create filename (sanitize ID for filename)
    safe_id = "".join(c if c.isalnum() or c in '-_' else '_' for c in str(transaction_id))
    filename = f"transaction_{safe_id}.json"
    filepath = date_dir / filename
    
    # Save transaction as JSON
    with open(filepath, 'w') as f:
        json.dump(transaction, f, indent=2)
    
    return filepath


def detect_format(content):
    """
    Detect if content is JSON or text format.
    
    Returns:
        'json' if content appears to be JSON
        'text' if content appears to be text format (Java/Kotlin object string)
    """
    content = content.strip()
    
    # If it starts with [ or {, it's likely JSON
    if content.startswith('[') or content.startswith('{'):
        try:
            json.loads(content)
            return 'json'
        except json.JSONDecodeError:
            pass
    
    # If it contains "Transaction[" it's text format
    if 'Transaction[' in content:
        return 'text'
    
    # Try to parse as JSON anyway
    try:
        json.loads(content)
        return 'json'
    except json.JSONDecodeError:
        pass
    
    # Default to text format
    return 'text'


def load_json_data(content):
    """Load transaction data from JSON format."""
    # Try to parse as JSON array
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Try JSONL format (one JSON object per line)
        data = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        if not data:
            raise ValueError("Could not parse JSON data. Check file format.")
    
    # Handle single object (wrap in array)
    if isinstance(data, dict):
        data = [data]
    
    return data


def load_text_data(content):
    """Load transaction data from text format (Java/Kotlin object strings)."""
    transactions = parse_multiple_transactions(content)
    
    if not transactions:
        raise ValueError(
            "Could not parse text data. "
            "Ensure each transaction starts with 'Transaction[' and ends with ']'."
        )
    
    return transactions


def load_raw_data():
    """
    Load raw transaction data from available files.
    
    Checks for:
    1. raw_transactions.txt (text format - preferred if exists)
    2. raw_transactions.json (JSON format)
    
    Returns:
        Tuple of (transactions list, source file path)
    """
    # Check for text file first (text format)
    if RAW_TEXT_FILE.exists():
        print(f"Found text format file: {RAW_TEXT_FILE.name}")
        with open(RAW_TEXT_FILE, 'r') as f:
            content = f.read().strip()
        
        if content:
            format_type = detect_format(content)
            print(f"Detected format: {format_type}")
            
            if format_type == 'text':
                return load_text_data(content), RAW_TEXT_FILE
            else:
                return load_json_data(content), RAW_TEXT_FILE
    
    # Check for JSON file
    if RAW_JSON_FILE.exists():
        print(f"Found JSON format file: {RAW_JSON_FILE.name}")
        with open(RAW_JSON_FILE, 'r') as f:
            content = f.read().strip()
        
        if content:
            format_type = detect_format(content)
            print(f"Detected format: {format_type}")
            
            if format_type == 'text':
                return load_text_data(content), RAW_JSON_FILE
            else:
                return load_json_data(content), RAW_JSON_FILE
    
    # No files found
    raise FileNotFoundError(
        f"No raw data files found.\n"
        f"Please create one of:\n"
        f"  - {RAW_TEXT_FILE} (for text format - Java/Kotlin object strings)\n"
        f"  - {RAW_JSON_FILE} (for JSON format)\n"
        f"See local_data/raw_transactions.example.* for format examples."
    )


def main():
    """Main conversion function."""
    print("=" * 60)
    print("Transaction Data Converter")
    print("=" * 60)
    print(f"Looking for data in: {PROJECT_ROOT / 'local_data'}")
    print(f"Output to: {OUTPUT_BASE}")
    print()
    
    # Load raw data
    try:
        transactions, source_file = load_raw_data()
        print(f"Loaded {len(transactions)} transaction(s) from {source_file.name}")
    except Exception as e:
        print(f"Error loading raw data: {e}")
        return 1
    
    print()
    
    # Convert each transaction
    converted = 0
    skipped = 0
    errors = []
    
    for i, transaction in enumerate(transactions, 1):
        try:
            filepath = convert_transaction(transaction, OUTPUT_BASE)
            if filepath:
                converted += 1
                print(f"  [{i}/{len(transactions)}] Converted: {filepath.relative_to(PROJECT_ROOT)}")
            else:
                skipped += 1
        except Exception as e:
            skipped += 1
            errors.append(f"Transaction {i}: {e}")
            print(f"  [{i}/{len(transactions)}] Error: {e}")
    
    # Summary
    print()
    print("=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"Total transactions: {len(transactions)}")
    print(f"Successfully converted: {converted}")
    print(f"Skipped/Errors: {skipped}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    if converted > 0:
        print(f"\n✓ Conversion complete! Files saved to {OUTPUT_BASE.relative_to(PROJECT_ROOT)}")
        print("\nTo use local data, run:")
        print("  USE_LOCAL_DATA=true streamlit run app.py")
    
    return 0 if converted > 0 else 1


if __name__ == "__main__":
    exit(main())
