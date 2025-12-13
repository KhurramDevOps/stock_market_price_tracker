# stock_loader.py
"""
Stock CSV loader (Steps 1-3)
- Pure Python (only csv & os)
- Functions:
    extract_stock_name_from_path(path)
    is_csv_file(path)
    file_exists(path)
    validate_csv_structure(path)
    read_csv_to_list_of_dicts(path)
    add_stock_to_registry(registry, stock_name, data, replace=True)
    upload_stock_interactive(registry)  # simple CLI helper
- Data stored as:
    all_stocks = {
        "TESLA": [ { "date": "...", "open": 123.4, "high": ..., "low": ..., "close": ..., "volume": ... }, ... ],
        ...
    }
"""

import os
import csv
import shutil

# ---------- Step 1 helpers ----------
def extract_stock_name_from_path(path: str) -> str:
    """
    Derive a stock name from filename.
    Example: 'data/nvidia.csv' -> 'NVIDIA'
    """
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    return name.strip().upper() if name else "UNKNOWN"

def is_csv_file(path: str) -> bool:
    """Simple check: path ends with .csv (case-insensitive)."""
    return isinstance(path, str) and path.lower().strip().endswith('.csv')

def file_exists(path: str) -> bool:
    """Check whether a file exists and is a file (not a directory)."""
    return os.path.isfile(path)

# ---------- Step 2 validation ----------
# Acceptable header synonyms mapped to standard keys
_HEADER_MAP = {
    'date': 'date',
    'timestamp': 'date',
    'open': 'open',
    'high': 'high',
    'low': 'low',
    'close': 'close',
    'adj close': 'close',
    'adjusted close': 'close',
    'close/last': 'close',
    'volume': 'volume',
}

def _normalize_header_name(h: str) -> str:
    """Lowercase and strip header for mapping."""
    return h.strip().lower()

def validate_csv_structure(path: str) -> (bool | dict):
    """
    Validate CSV file can be opened and has recognizable headers.
    Returns (is_valid, header_mapping) where header_mapping maps found csv header -> standard key.
    """
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

            # Map available headers to standard keys
            mapping = {}
            found_standard_keys = set()
            for col in header:
                norm = _normalize_header_name(col)
                if norm in _HEADER_MAP:
                    mapping[col] = _HEADER_MAP[norm]
                    found_standard_keys.add(_HEADER_MAP[norm])
                else:
                    # Unknown header -> store as-is but normalized
                    mapping[col] = norm

            # require at least 'date' and 'close' for meaningful operations
            if 'date' not in found_standard_keys or 'close' not in found_standard_keys:
                return False, {"error": "CSV must contain at least 'Date' and 'Close' (or synonyms like 'Adj Close') in header"}

            return True, mapping
    except Exception as e:
        return False, {"error": f"Unable to read file: {e}"}

# ---------- Step 3: Read CSV and store rows ----------
def _to_float_or_none(value: str):
    """Convert string to float, return None if empty or invalid."""
    if value is None:
        return None
    v = value.strip()
    if v == '':
        return None
    try:
        return float(v.replace(',', ''))  # remove thousand separators if any
    except Exception:
        return None

def read_csv_to_list_of_dicts(path: str):
    """
    Read CSV and return list of daily dictionaries with standardized keys:
    Each dict will have: date (string) and numeric open/high/low/close/volume where possible.
    """
    valid, meta = validate_csv_structure(path)
    if not valid:
        raise ValueError(f"CSV validation failed: {meta.get('error')}")

    header_map = meta  # maps original header -> standard key or normalized name

    rows = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for raw in reader:
            # Build standardized row
            row = {}
            for orig_col, val in raw.items():
                std_key = header_map.get(orig_col, _normalize_header_name(orig_col))
                if std_key == 'date':
                    row['date'] = val.strip() if val is not None else ''
                elif std_key in ('open', 'high', 'low', 'close'):
                    row[std_key] = _to_float_or_none(val)
                elif std_key == 'volume':
                    # volume might be integer; store as float or None
                    vol = _to_float_or_none(val)
                    row['volume'] = int(vol) if vol is not None and vol.is_integer() else vol
                else:
                    # keep any other columns too (optional)
                    row[std_key] = val.strip() if isinstance(val, str) else val
            # Basic sanity: require date present
            if 'date' not in row or not row['date']:
                # skip malformed row or raise depending on your policy
                continue
            rows.append(row)

    # Preserve file order. If you need descending/ascending by date, we'll sort later in summary step.
    return rows

def add_stock_to_registry(registry: dict, stock_name: str, data: list, replace: bool = True) -> None:
    """
    Add parsed stock data to the registry dict.
    - registry: dict (mutated)
    - stock_name: str (key)
    - data: list of day-dicts as returned by read_csv_to_list_of_dicts
    - replace: if False and stock exists, do nothing (or could append)
    """
    key = stock_name.strip().upper()
    if key in registry and not replace:
        # keep existing
        return
    registry[key] = data

# ---------- Simple CLI helper ----------
def upload_stock_interactive(registry: dict):
    """
    Small interactive helper to upload a stock CSV via input().
    It will:
    - ask path
    - validate
    - parse
    - add to registry using filename as stock name
    """
    path = input("Enter path to stock CSV (local file): ").strip()
    valid, meta = validate_csv_structure(path)
    if not valid:
        print("Validation failed:", meta.get('error'))
        return

    name = extract_stock_name_from_path(path)
    print(f"Detected stock name: {name}")

    # ask whether to replace if exists
    if name.upper() in registry:
        ans = input(f"Stock '{name}' already exists. Replace? (y/n): ").strip().lower()
        if ans != 'y':
            print("Upload cancelled.")
            return

    try:
        data = read_csv_to_list_of_dicts(path)
        add_stock_to_registry(registry, name, data, replace=True)
        print(f"Uploaded {name}. Rows loaded: {len(data)}")
    except Exception as e:
        print("Error while reading CSV:", e)

# ---------- CLI Menu Functions ----------
def list_stocks(registry: dict):
    """List all loaded stocks with row counts."""
    if not registry:
        print("No stocks loaded.")
        return
    for name, data in registry.items():
        print(f"{name}: {len(data)} rows")

def upload_stock(registry: dict):
    """Interactive upload of a stock CSV."""
    path = input("Enter full path to the CSV file (or 'cancel' to return): ").strip()
    if path.lower() == 'cancel':
        print("Upload cancelled.")
        return
    if not file_exists(path):
        print("Validation failed: File does not exist")
        return
    if not is_csv_file(path):
        print("Validation failed: File is not a CSV")
        return
    valid, meta = validate_csv_structure(path)
    if not valid:
        print(f"Validation failed: {meta.get('error')}")
        return
    stock_name = extract_stock_name_from_path(path)
    key = stock_name.upper()
    if key in registry:
        while True:
            ans = input(f"Stock '{stock_name}' already exists. (R)eplace / (K)eep existing / (C)ancel? ").strip().lower()
            if ans == 'r':
                dest = os.path.join("data", os.path.basename(path))
                os.makedirs("data", exist_ok=True)
                shutil.copy(path, dest)
                rows = read_csv_to_list_of_dicts(dest)
                add_stock_to_registry(registry, stock_name, rows, replace=True)
                print(f"Uploaded {stock_name} — {len(rows)} rows")
                break
            elif ans == 'k':
                print("Kept existing stock.")
                break
            elif ans == 'c':
                print("Upload cancelled.")
                break
            else:
                print("Invalid choice. Enter R, K, or C.")
    else:
        dest = os.path.join("data", os.path.basename(path))
        os.makedirs("data", exist_ok=True)
        shutil.copy(path, dest)
        rows = read_csv_to_list_of_dicts(dest)
        add_stock_to_registry(registry, stock_name, rows)
        print(f"Uploaded {stock_name} — {len(rows)} rows")

def reload_stock(registry: dict):
    """Reload a stock from disk."""
    if not registry:
        print("No stocks loaded to reload.")
        return
    print("Loaded stocks:")
    names = list(registry.keys())
    for i, name in enumerate(names, 1):
        print(f"{i}) {name}")
    choice = input("Enter stock name or number to reload: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(names):
            stock_name = names[idx]
        else:
            print("Invalid number.")
            return
    else:
        stock_name = choice.upper()
        if stock_name not in registry:
            print(f"Stock '{stock_name}' not loaded.")
            return
    data_dir = "data"
    filename = None
    for f in os.listdir(data_dir):
        if extract_stock_name_from_path(f).upper() == stock_name:
            filename = f
            break
    if not filename:
        print(f"Local file for {stock_name} not found in data/; please upload first.")
        return
    path = os.path.join(data_dir, filename)
    try:
        rows = read_csv_to_list_of_dicts(path)
        add_stock_to_registry(registry, stock_name, rows, replace=True)
        print(f"Reloaded {stock_name} — {len(rows)} rows")
    except Exception as e:
        print(f"Error reloading {stock_name}: {e}")

def preview_stock(registry: dict):
    """Show sample rows for a stock."""
    if not registry:
        print("No stocks loaded to preview.")
        return
    print("Loaded stocks:")
    names = list(registry.keys())
    for i, name in enumerate(names, 1):
        print(f"{i}) {name}")
    choice = input("Enter stock name or number to preview: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(names):
            stock_name = names[idx]
        else:
            print("Invalid number.")
            return
    else:
        stock_name = choice.upper()
        if stock_name not in registry:
            print(f"Stock '{stock_name}' not loaded.")
            return
    data = registry[stock_name]
    n = min(5, len(data))
    print(f"First {n} rows for {stock_name}:")
    print("Date\t\tOpen\tHigh\tLow\tClose\tVolume")
    for row in data[:n]:
        date = row.get('date', '')
        open_ = row.get('open', '')
        high = row.get('high', '')
        low = row.get('low', '')
        close = row.get('close', '')
        volume = row.get('volume', '')
        print(f"{date}\t{open_}\t{high}\t{low}\t{close}\t{volume}")

def generate_stock_summary(registry, stock_name):
    """
    Generates a 10-day statistical summary for a specific stock.
    Logic:
    1. Check if stock exists.
    2. Slice the list to get the last 10 days.
    3. Calculate change, % change, max high, min low, and avg volume.
    4. Print the result.
    """
    # Normalize the stock name input
    key = stock_name.strip().upper()

    # 1. Validation: Does stock exist?
    if key not in registry:
        print(f"Error: Stock '{key}' not found in registry.")
        return

    data = registry[key]
    total_rows = len(data)

    if total_rows == 0:
        print(f"Error: No data available for {key}.")
        return

    # 2. Slicing: Get the last 10 days (or fewer if data is short)
    days_to_analyze = 10
    if total_rows < 10:
        print(f"Note: Only {total_rows} days of data available. Analyzing all.")
        days_to_analyze = total_rows

    # data[:days_to_analyze] gives us the first 10 items in the list
    recent_data = data[:days_to_analyze]

    try:
        # Get Start and End values
        current_row = recent_data[0]   
        start_row = recent_data[-1]    

        current_close = current_row.get('close')
        start_close = start_row.get('close')

        # Check for missing data before math
        if start_close is None or current_close is None:
            print("Error: 'Close' price data is missing for this stock.")
            return

        # 3. Calculations
        price_change = current_close - start_close
        
        # Calculate Percentage: (Change / Original) * 100
        if start_close != 0:
            pct_change = (price_change / start_close) * 100
        else:
            pct_change = 0.0

        # Loop through the slice to find High, Low, and Total Volume
        highest_price = -1.0
        lowest_price = float('inf') # Start with a very high number
        total_volume = 0
        
        # We assume the first row has valid data to initialize, 
        # but the loop is safer if we check each row.
        valid_vol_count = 0

        for row in recent_data:
            # Find Max High
            h = row.get('high')
            if h is not None and h > highest_price:
                highest_price = h
            
            # Find Min Low
            l = row.get('low')
            if l is not None and l < lowest_price:
                lowest_price = l
            
            # Sum Volume
            v = row.get('volume')
            if v is not None:
                total_volume += v
                valid_vol_count += 1

        # Calculate Average Volume
        if valid_vol_count > 0:
            avg_volume = total_volume / valid_vol_count
        else:
            avg_volume = 0

        # 4. Display Output
        print(f"\n{'='*40}")
        print(f"       STOCK SUMMARY: {key}")
        print(f"{'='*40}")
        print(f"Analysis Period:   Last {days_to_analyze} Days")
        print(f"Date Range:        {start_row.get('date')} to {current_row.get('date')}")
        print("-" * 40)
        print(f"Current Price:     {current_close:,.2f}")
        print(f"Price Change:      {price_change:+,.2f}")
        print(f"Percent Change:    {pct_change:+.2f}%")
        print("-" * 40)
        print(f"10-Day High:       {highest_price:,.2f}")
        print(f"10-Day Low:        {lowest_price:,.2f}")
        print(f"Avg Volume:        {int(avg_volume):,}")
        print(f"{'='*40}\n")

    except Exception as e:
        print(f"An error occurred while calculating summary: {e}")

# ---------- Example usage ----------
if __name__ == "__main__":
    # Registry holds all loaded stocks
    all_stocks = {}

    # Preload stocks from data/
    data_dir = "data/"
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            path = os.path.join(data_dir, filename)
            if is_csv_file(path) and file_exists(path):
                try:
                    valid, meta = validate_csv_structure(path)
                    if valid:
                        rows = read_csv_to_list_of_dicts(path)
                        stock_name = extract_stock_name_from_path(path)
                        add_stock_to_registry(all_stocks, stock_name, rows)
                        print(f"Preloaded {stock_name}: {len(rows)} rows")
                    else:
                        print(f"Skipped {filename}: {meta.get('error')}")
                except Exception as e:
                    print(f"Error preloading {filename}: {e}")
    else:
        print("Data directory not found; starting with no stocks.")

    # Main menu loop
    while True:
        print("\nMain Menu — choose an option:")
        print("1) List loaded stocks")
        print("2) Upload stock CSV")
        print("3) Reload a stock from disk")
        print("4) Show sample rows (preview)")
        print("5) Generate stock summary")
        print("6) Exit")
        choice = input("Enter choice (1-6): ").strip()
        try:
            if choice == '1':
                list_stocks(all_stocks)
            elif choice == '2':
                upload_stock(all_stocks)
            elif choice == '3':
                reload_stock(all_stocks)
            elif choice == '4':
                preview_stock(all_stocks)
            elif choice == '5':
                # Prompt for stock name
                if not all_stocks:
                    print("No stocks loaded to summarize.")
                else:
                    print("Loaded stocks:")
                    names = list(all_stocks.keys())
                    for i, name in enumerate(names, 1):
                        print(f"{i}) {name}")
                    stock_choice = input("Enter stock name or number to summarize: ").strip()
                    if stock_choice.isdigit():
                        idx = int(stock_choice) - 1
                        if 0 <= idx < len(names):
                            stock_name = names[idx]
                            generate_stock_summary(all_stocks, stock_name)
                        else:
                            print("Invalid number.")
                    else:
                        stock_name = stock_choice.upper()
                        if stock_name in all_stocks:
                            generate_stock_summary(all_stocks, stock_name)
                        else:
                            print(f"Stock '{stock_name}' not loaded.")
            elif choice == '6':
                print(f"Goodbye — {len(all_stocks)} stocks loaded.")
                break
            else:
                print("Invalid choice. Try again.")
        except Exception as e:
            print(f"An error occurred: {e}. Please try again.")
# stock_loader.py
