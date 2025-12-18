# Local Data Directory

This directory contains local transaction data for development and testing.

## Quick Start Workflow

1. **Paste raw transaction data** into `raw_transactions.txt`
2. **Start the app** (if not running): `./start-local-dev.sh`
3. **Click "Refresh & Convert Data"** in the sidebar
4. Your transactions will be parsed and displayed!

## Supported Formats

### Text Format (Java/Kotlin Object Strings) - Recommended

Paste raw transaction data directly from logs or debugging output into `raw_transactions.txt`.

**File**: `raw_transactions.txt`

**Format**: One or more transactions starting with `Transaction[...]`

```
Transaction[type=Optional[transaction], id=xxx, createdAt=2024-12-16T10:30:00Z, status=TransactionStatus [value=authorization_succeeded], amount=1591, currency=CAD, ...]

Transaction[type=Optional[transaction], id=yyy, createdAt=2024-12-16T11:00:00Z, status=TransactionStatus [value=authorization_failed], amount=2500, currency=CAD, ...]
```

**Multiple Transactions**: Just paste multiple `Transaction[...]` blocks. You can separate them with blank lines or put them consecutively - the parser will detect each one.

See `raw_transactions.example.txt` for a complete example.

### JSON Format (Alternative)

Standard JSON array of transaction objects.

**File**: `raw_transactions.json`

```json
[
  {
    "timestamp": "2024-12-16T10:30:00",
    "transaction_id": "TXN-001",
    "status": "success",
    "amount": 99.99,
    "details": {...}
  }
]
```

See `raw_transactions.example.json` for an example.

## Files

| File | Description |
|------|-------------|
| `raw_transactions.txt` | Paste raw text-format transaction data here |
| `raw_transactions.json` | Paste JSON-format transaction data here |
| `raw_transactions.example.txt` | Example text format |
| `raw_transactions.example.json` | Example JSON format |
| `logs/` | Converted transaction files (auto-generated) |

## How It Works

When you click **"Refresh & Convert Data"** in the app sidebar:

1. The app reads `raw_transactions.txt`
2. Parses each `Transaction[...]` block
3. Converts to S3-compatible JSON format
4. Saves to `logs/YYYY/MM/DD/transaction_{id}.json`
5. Loads and displays the transactions

The sidebar shows how many transactions were found in your `.txt` file.

## Manual Conversion (Optional)

If you prefer to run conversion separately:

```bash
python scripts/convert_raw_to_local.py
```

This does the same conversion but outside the app.

## Text Format Field Mapping

When parsing text format, the converter maps fields:

| Text Format Field | JSON Output Field |
|-------------------|-------------------|
| `id` | `transaction_id` |
| `createdAt` | `timestamp` |
| `status` (TransactionStatus [value=...]) | `status` (normalized) |
| `amount` | `amount` (converted from cents to dollars) |
| `currency` | `currency` |
| Other fields | Stored in `details` |

### Status Normalization

| Raw Status | Normalized Status |
|------------|-------------------|
| `authorization_succeeded` | `success` |
| `authorization_failed` | `failed` |
| Other values | Preserved as-is |

### Amount Conversion

- Integer amounts (e.g., `1591`) are assumed to be in cents and converted to dollars (`15.91`)
- Decimal amounts are used as-is

## Output Structure

Converted files follow the S3 structure:

```
logs/
└── YYYY/
    └── MM/
        └── DD/
            └── transaction_{id}.json
```
