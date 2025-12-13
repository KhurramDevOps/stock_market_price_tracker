import os
import csv
import shutil


# ---------- Internal Helpers ----------
_HEADER_MAP = {
    'date': 'date', 'timestamp': 'date',
    'open': 'open', 'high': 'high', 'low': 'low',
    'close': 'close', 'adj close': 'close', 'adjusted close': 'close',
    'close/last': 'close', 'volume': 'volume',
}

def _normalize_header_name(h: str) -> str:
    return h.strip().lower()

def _to_float_or_none(value: str):
    if value is None: return None
    v = value.strip()
    if v == '': return None
    try:
        # FIX: Remove BOTH commas AND dollar signs
        clean_value = v.replace(',', '').replace('$', '')
        return float(clean_value)
    except Exception:
        return None

# ---------- Public Functions ----------
def extract_stock_name_from_path(path: str) -> str:
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    return name.strip().upper() if name else "UNKNOWN"

def is_csv_file(path: str) -> bool:
    return isinstance(path, str) and path.lower().strip().endswith('.csv')

def file_exists(path: str) -> bool:
    return os.path.isfile(path)

def validate_csv_structure(path: str) -> (bool | dict):
    if not file_exists(path):
        return False, {"error": "File does not exist"}
    if not is_csv_file(path):
        return False, {"error": "File is not a CSV"}

    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return False, {"error": "CSV has no header / is empty"}

            mapping = {}
            found_standard_keys = set()
            for col in header:
                norm = _normalize_header_name(col)
                if norm in _HEADER_MAP:
                    mapping[col] = _HEADER_MAP[norm]
                    found_standard_keys.add(_HEADER_MAP[norm])
                else:
                    mapping[col] = norm

            if 'date' not in found_standard_keys or 'close' not in found_standard_keys:
                return False, {"error": "CSV must contain at least 'Date' and 'Close'"}

            return True, mapping
    except Exception as e:
        return False, {"error": f"Unable to read file: {e}"}

def read_csv_to_list_of_dicts(path: str):
    valid, meta = validate_csv_structure(path)
    if not valid:
        raise ValueError(f"CSV validation failed: {meta.get('error')}")

    header_map = meta
    rows = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {}
            for orig_col, val in raw.items():
                std_key = header_map.get(orig_col, _normalize_header_name(orig_col))
                if std_key == 'date':
                    row['date'] = val.strip() if val is not None else ''
                elif std_key in ('open', 'high', 'low', 'close'):
                    row[std_key] = _to_float_or_none(val)
                elif std_key == 'volume':
                    vol = _to_float_or_none(val)
                    row['volume'] = int(vol) if vol is not None and vol.is_integer() else vol
                else:
                    row[std_key] = val.strip() if isinstance(val, str) else val
            
            if 'date' not in row or not row['date']:
                continue
            rows.append(row)
    return rows

def add_stock_to_registry(registry: dict, stock_name: str, data: list, replace: bool = True) -> None:
    key = stock_name.strip().upper()
    if key in registry and not replace:
        return
    registry[key] = data



def save_uploaded_file(source_path):
    """
    Copies a file from source_path to the 'data/' folder.
    Returns the new path if successful.
    """
    try:
        dest_dir = "data"
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(source_path))
        shutil.copy(source_path, dest_path)
        return dest_path
    except Exception as e:
        print(f"System Error copying file: {e}")
        return None