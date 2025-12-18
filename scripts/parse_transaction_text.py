#!/usr/bin/env python3
"""
Parse Java/Kotlin object string format transaction data.

This module parses transaction data in the format:
Transaction[type=Optional[transaction], id=xxx, createdAt=xxx, ...]

And converts it to JSON format expected by the application.

Generates three representations:
- raw_text: Original text as-is
- json_full: All fields including nulls
- json_compact: Filtered version without nulls
"""

import re
from typing import Dict, Any, Optional, List, Union


def parse_value_recursive(value: str) -> Any:
    """
    Recursively parse a value string into its JSON representation.
    Handles nested objects, arrays, and wrapper types.
    Preserves null values as None.
    
    Args:
        value: Raw value string from the transaction
        
    Returns:
        Parsed value (dict, list, string, number, bool, or None)
    """
    if value is None:
        return None
    
    value = value.strip()
    
    # Handle empty strings
    if value == '':
        return None
    
    # Handle explicit null values
    if value.lower() in ['null', 'none']:
        return None
    
    # Handle boolean values
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # Handle JsonNullable[null] -> None
    if value == 'JsonNullable[null]':
        return None
    
    # Handle Optional[null] -> None
    if value == 'Optional[null]':
        return None
    
    # Handle empty array
    if value == '[]':
        return []
    
    # Handle TypeName [value=xxx] format (e.g., TransactionStatus [value=authorization_succeeded])
    value_match = re.match(r'^(\w+)\s*\[value=([^\]]+)\]$', value)
    if value_match:
        return value_match.group(2).strip()
    
    # Handle Optional[xxx] - unwrap and parse inner value
    optional_match = re.match(r'^Optional\[(.+)\]$', value, re.DOTALL)
    if optional_match:
        inner = optional_match.group(1)
        if inner.lower() == 'null':
            return None
        return parse_value_recursive(inner)
    
    # Handle JsonNullable[xxx] - unwrap and parse inner value
    nullable_match = re.match(r'^JsonNullable\[(.+)\]$', value, re.DOTALL)
    if nullable_match:
        inner = nullable_match.group(1)
        if inner.lower() == 'null':
            return None
        return parse_value_recursive(inner)
    
    # Handle nested object with TypeName[...] format (e.g., TransactionBuyer[...])
    nested_match = re.match(r'^(\w+)\[(.+)\]$', value, re.DOTALL)
    if nested_match:
        type_name = nested_match.group(1)
        inner_content = nested_match.group(2)
        # Parse the inner content as fields
        parsed_fields = parse_fields_from_content(inner_content)
        if parsed_fields:
            # Add the type name
            parsed_fields['_type'] = type_name
            return parsed_fields
    
    # Handle array with items [..., ...]
    if value.startswith('[') and value.endswith(']'):
        inner = value[1:-1].strip()
        if not inner:
            return []
        # Parse array items
        return parse_array_items(inner)
    
    # Handle map/dict format {key=value, ...}
    if value.startswith('{') and value.endswith('}'):
        inner = value[1:-1].strip()
        if not inner:
            return {}
        return parse_map_items(inner)
    
    # Try to parse as number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    # Return as string
    return value


def parse_fields_from_content(content: str) -> Dict[str, Any]:
    """
    Parse field=value pairs from content string, handling nested brackets.
    
    Args:
        content: String containing field=value pairs
        
    Returns:
        Dictionary of field names to parsed values
    """
    fields = {}
    
    i = 0
    current_field = ""
    current_value = ""
    in_field = True
    bracket_depth = 0
    
    while i < len(content):
        char = content[i]
        
        if char == '[':
            bracket_depth += 1
            if in_field:
                current_field += char
            else:
                current_value += char
        elif char == ']':
            bracket_depth -= 1
            if in_field:
                current_field += char
            else:
                current_value += char
        elif char == '{':
            bracket_depth += 1
            if in_field:
                current_field += char
            else:
                current_value += char
        elif char == '}':
            bracket_depth -= 1
            if in_field:
                current_field += char
            else:
                current_value += char
        elif char == '=' and bracket_depth == 0 and in_field:
            in_field = False
        elif char == ',' and bracket_depth == 0:
            # End of field-value pair
            field_name = current_field.strip()
            if field_name:
                fields[field_name] = parse_value_recursive(current_value.strip())
            current_field = ""
            current_value = ""
            in_field = True
        else:
            if in_field:
                current_field += char
            else:
                current_value += char
        
        i += 1
    
    # Don't forget the last field
    field_name = current_field.strip()
    if field_name:
        fields[field_name] = parse_value_recursive(current_value.strip())
    
    return fields


def parse_array_items(content: str) -> List[Any]:
    """
    Parse array items from content string.
    
    Args:
        content: String containing array items
        
    Returns:
        List of parsed items
    """
    items = []
    
    i = 0
    current_item = ""
    bracket_depth = 0
    
    while i < len(content):
        char = content[i]
        
        if char in '[{':
            bracket_depth += 1
            current_item += char
        elif char in ']}':
            bracket_depth -= 1
            current_item += char
        elif char == ',' and bracket_depth == 0:
            item = current_item.strip()
            if item:
                items.append(parse_value_recursive(item))
            current_item = ""
        else:
            current_item += char
        
        i += 1
    
    # Don't forget the last item
    item = current_item.strip()
    if item:
        items.append(parse_value_recursive(item))
    
    return items


def parse_map_items(content: str) -> Dict[str, Any]:
    """
    Parse map items from {key=value, ...} format.
    
    Args:
        content: String containing map items
        
    Returns:
        Dictionary of parsed items
    """
    return parse_fields_from_content(content)


def remove_nulls(obj: Any) -> Any:
    """
    Recursively remove null values from a dictionary or list.
    
    Args:
        obj: Object to filter
        
    Returns:
        Filtered object without null values
    """
    if isinstance(obj, dict):
        return {
            k: remove_nulls(v) 
            for k, v in obj.items() 
            if v is not None and (not isinstance(v, dict) or v) and (not isinstance(v, list) or v)
        }
    elif isinstance(obj, list):
        return [remove_nulls(item) for item in obj if item is not None]
    return obj


def normalize_status(status: Any) -> str:
    """
    Normalize transaction status to standard values.
    """
    if status is None:
        return 'unknown'
    
    status_str = str(status).lower()
    
    if 'succeeded' in status_str or 'success' in status_str:
        return 'success'
    elif 'failed' in status_str or 'failure' in status_str:
        return 'failed'
    elif 'pending' in status_str:
        return 'pending'
    elif 'cancelled' in status_str or 'canceled' in status_str:
        return 'cancelled'
    elif 'refunded' in status_str:
        return 'refunded'
    elif 'voided' in status_str:
        return 'voided'
    
    return str(status)


def convert_amount(amount: Any) -> float:
    """
    Convert amount to float.
    Assumes integer values >= 100 are in cents and need to be divided by 100.
    """
    if amount is None:
        return 0.0
    
    try:
        value = float(amount)
        # If it's a whole number >= 100, assume it's in cents
        if value == int(value) and abs(value) >= 100:
            return value / 100.0
        return value
    except (ValueError, TypeError):
        return 0.0


def parse_transaction_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single transaction from text format to JSON format.
    
    Returns a dictionary with:
    - transaction_id, timestamp, status, amount, currency (for display/filtering)
    - raw_text: Original text as-is
    - json_full: All parsed fields including nulls
    - json_compact: Parsed fields with nulls removed
    
    Args:
        text: The transaction string in Java/Kotlin object format
        
    Returns:
        Dictionary with transaction data, or None if parsing fails
    """
    if not text or not text.strip():
        return None
    
    text = text.strip()
    
    # Store the raw text
    raw_text = text
    
    # Parse the Transaction[...] wrapper
    match = re.match(r'^\s*Transaction\[(.+)\]\s*$', text, re.DOTALL)
    if not match:
        return None
    
    content = match.group(1)
    
    # Parse ALL fields recursively
    json_full = parse_fields_from_content(content)
    
    if not json_full:
        return None
    
    # Create compact version without nulls
    json_compact = remove_nulls(json_full)
    
    # Extract key fields for the main result (used for display/metrics)
    result = {}
    
    # Transaction ID
    if 'id' in json_full:
        result['transaction_id'] = json_full['id']
    
    # Timestamp
    if 'createdAt' in json_full:
        result['timestamp'] = json_full['createdAt']
    elif 'updatedAt' in json_full:
        result['timestamp'] = json_full['updatedAt']
    
    # Status (normalized)
    if 'status' in json_full:
        result['status'] = normalize_status(json_full['status'])
    
    # Amount (converted from cents)
    if 'amount' in json_full:
        result['amount'] = convert_amount(json_full['amount'])
    
    # Currency
    if 'currency' in json_full:
        result['currency'] = json_full['currency']
    
    # Add the three representations
    result['raw_text'] = raw_text
    result['json_full'] = json_full
    result['json_compact'] = json_compact
    
    return result


def parse_multiple_transactions(text: str) -> List[Dict[str, Any]]:
    """
    Parse multiple transactions from text.
    
    Transactions can be separated by:
    - Blank lines
    - Each on its own line starting with 'Transaction['
    
    Args:
        text: String containing one or more transactions
        
    Returns:
        List of parsed transaction dictionaries
    """
    transactions = []
    
    # Split by 'Transaction[' to find individual transactions
    parts = re.split(r'(?=Transaction\[)', text)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        parsed = parse_transaction_text(part)
        if parsed:
            transactions.append(parsed)
    
    return transactions


def main():
    """Test the parser with sample data."""
    import json
    
    sample = '''Transaction[type=Optional[transaction], id=2eb38251-7909-4204-9f76-4306738990b2, reconciliationId=1Q7gL6MYhzBJkN54ZIXVSs, merchantAccountId=secure-fields-capture, currency=CAD, amount=1591, status=TransactionStatus [value=authorization_succeeded], authorizedAmount=1591, capturedAmount=0, refundedAmount=0, settledCurrency=JsonNullable[null], settledAmount=0, settled=false, country=JsonNullable[CA], createdAt=2025-12-16T20:23:36.201957Z, updatedAt=2025-12-16T20:23:37.664110Z]'''
    
    result = parse_transaction_text(sample)
    if result:
        print("=== Transaction ID ===")
        print(result.get('transaction_id'))
        print("\n=== JSON Full (with nulls) ===")
        print(json.dumps(result.get('json_full'), indent=2))
        print("\n=== JSON Compact (without nulls) ===")
        print(json.dumps(result.get('json_compact'), indent=2))
    else:
        print("Failed to parse transaction")


if __name__ == "__main__":
    main()
