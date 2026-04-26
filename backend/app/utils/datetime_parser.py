from datetime import datetime
from email.utils import parsedate_to_datetime

def parse_datetime(value_str):
    """Parse datetime string in multiple formats"""
    if not value_str or value_str.lower() == 'null':
        return None
    
    value_str = str(value_str).strip()
    dt = None
    
    # Try ISO format first
    try:
        dt = datetime.fromisoformat(value_str.replace('Z', '+00:00'))
    except:
        pass
    
    # Try HTTP date format (Sat, 10 Feb 2024 09:30:00 GMT)
    if not dt:
        try:
            dt = parsedate_to_datetime(value_str)
        except:
            pass
    
    # Try common datetime formats
    if not dt:
        for fmt in ['%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
            try:
                dt = datetime.strptime(value_str, fmt)
                break
            except:
                pass
    
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return value_str

def format_datetime_fields(data, datetime_fields):
    """Format all datetime fields in a dictionary"""
    for field in datetime_fields:
        if field in data and data[field]:
            try:
                data[field] = parse_datetime(data[field])
            except Exception as parse_error:
                print(f"Error parsing {field}: {parse_error}")
    
    # Handle empty strings as NULL
    for key in data:
        if data[key] == '':
            data[key] = None
    
    return data
