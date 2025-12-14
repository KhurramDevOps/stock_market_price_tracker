# main.py
import os
import stock_loader
import stock_analysis
import stock_query
import stock_watchlist
import stock_portfolio

# ---------- Helper: Select Stock by Name OR Number ----------
def _select_stock(registry):
    """
    Helper to list stocks and let user pick by Number (1) or Name (APPLE).
    Returns the selected stock name (key) or None if invalid.
    """
    if not registry:
        print("No stocks loaded.")
        return None

    print("Loaded stocks:")
    names = list(registry.keys())
    for i, name in enumerate(names, 1):
        print(f"{i}) {name}")

    choice = input("Enter stock name or number: ").strip()
    
    # 1. Try to handle as a Number (e.g., "1")
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(names):
            return names[idx]
        else:
            print("Invalid number.")
            return None
    
    # 2. Handle as a Name (e.g., "APPLE")
    key = choice.upper()
    if key in registry:
        return key
    else:
        print(f"Stock '{key}' not found.")
        return None

# ---------- Menu Actions (Formatted to match your original) ----------

def list_stocks(registry: dict):
    if not registry:
        print("No stocks loaded.")
        return
    for name, data in registry.items():
        print(f"{name}: {len(data)} rows")

def upload_stock_action(registry: dict):
    # 1. Get Path
    path = input("Enter full path to the CSV file (or 'cancel' to return): ").strip()
    if path.lower() == 'cancel':
        print("Upload cancelled.")
        return

    # 2. Validate
    valid, meta = stock_loader.validate_csv_structure(path)
    if not valid:
        print(f"Validation failed: {meta.get('error')}")
        return

    # 3. Check for Duplicates
    stock_name = stock_loader.extract_stock_name_from_path(path)
    key = stock_name.upper()

    if key in registry:
        while True:
            ans = input(f"Stock '{stock_name}' already exists. (R)eplace / (K)eep existing / (C)ancel? ").lower()
            if ans == 'r':
                break
            elif ans == 'k':
                print("Kept existing stock.")
                return
            elif ans == 'c':
                print("Upload cancelled.")
                return
            else:
                print("Invalid choice. Please enter R, K, or C.")

    # 4. Perform the Upload
    print(f"Uploading {stock_name}...")
    new_path = stock_loader.save_uploaded_file(path)  # <--- Calls the loader here!
    
    if new_path:
        try:
            rows = stock_loader.read_csv_to_list_of_dicts(new_path)
            stock_loader.add_stock_to_registry(registry, stock_name, rows, replace=True)
            print(f"Successfully uploaded {stock_name} — {len(rows)} rows.")
        except Exception as e:
            print(f"Error reading uploaded file: {e}")



def reload_stock_action(registry: dict):
    # Use our helper to pick the stock
    name = _select_stock(registry)
    if not name:
        return

    # Find the file
    filename = None
    data_dir = "data"
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if stock_loader.extract_stock_name_from_path(f) == name:
                filename = f
                break
    
    if filename:
        path = os.path.join(data_dir, filename)
        try:
            rows = stock_loader.read_csv_to_list_of_dicts(path)
            stock_loader.add_stock_to_registry(registry, name, rows, replace=True)
            print(f"Reloaded {name} — {len(rows)} rows")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Local file for {name} not found in data/; please upload first.")

def preview_stock_action(registry: dict):
    # Use our helper to pick the stock
    name = _select_stock(registry)
    if not name:
        return

    data = registry[name]
    n = min(5, len(data))
    print(f"First {n} rows for {name}:")
    # THE NICE TABLE FORMATTING YOU WANTED
    print("Date\t\tOpen\tHigh\tLow\tClose\tVolume")
    for row in data[:n]:
        d = row.get('date', '')
        o = row.get('open', '')
        h = row.get('high', '')
        l = row.get('low', '')
        c = row.get('close', '')
        v = row.get('volume', '')
        print(f"{d}\t{o}\t{h}\t{l}\t{c}\t{v}")

# ---------- Main Execution ----------

if __name__ == "__main__":
    all_stocks = {}

    # 1. Preload stocks
    data_dir = "data/"
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            path = os.path.join(data_dir, filename)
            if stock_loader.is_csv_file(path):
                try:
                    rows = stock_loader.read_csv_to_list_of_dicts(path)
                    s_name = stock_loader.extract_stock_name_from_path(path)
                    stock_loader.add_stock_to_registry(all_stocks, s_name, rows)
                    print(f"Preloaded {s_name}: {len(rows)} rows")
                except Exception:
                    pass
    else:
        os.makedirs(data_dir, exist_ok=True)
        print("Data directory not found; starting with no stocks.")

    # 2. Main Menu Loop
    while True:
        print("\nMain Menu — choose an option:")
        print("1) List loaded stocks")
        print("2) Upload stock CSV")
        print("3) Reload a stock from disk")
        print("4) Show sample rows (preview)")
        print("5) Generate stock summary")
        print("6) My Watchlist")
        print("7) Strategy Advisor (Buy/Sell Signals)")
        print("8) Portfolio Performance Tracker") 
        print("9) Exit")

        choice = input("Enter choice (1-9): ").strip()

        if choice == '1':
            list_stocks(all_stocks)
        elif choice == '2':
            upload_stock_action(all_stocks)
        elif choice == '3':
            reload_stock_action(all_stocks)
        elif choice == '4':
            preview_stock_action(all_stocks)
        elif choice == '5':
            s_name = _select_stock(all_stocks)
            if s_name:
                # 1. This prints the summary AND returns the data
                data_to_save = stock_analysis.generate_stock_summary(all_stocks, s_name)
                
                # 2. Ask User if they want to save
                if data_to_save:
                    save_ans = input("Do you want to save this summary? (y/n): ").strip().lower()
                    if save_ans == 'y':
                        # 3. Create filename and call loader
                        filename = f"Summary_{s_name}.csv"
                        saved_path = stock_loader.save_csv_file(filename, data_to_save)
                        
                        if saved_path:
                            print(f"Success! Saved to: {saved_path}")
        elif choice == '6':
            # 1. Select Stock
            s_name = _select_stock(all_stocks)
            if s_name:
                # 2. Ask for Date
                date_input = input("Enter date  month/date/year (e.g., 12/12/2025): ").strip()
                
                # 3. Call the function from the new file
                result = stock_query.get_price_by_date(all_stocks, s_name, date_input)
                
                # 4. Show Result
                print(f"-" * 30)
                if isinstance(result, float):
                     print(f"Stock: {s_name}")
                     print(f"Date:  {date_input}")
                     print(f"Close: ${result:,.2f}")
                else:
                     print(result) # Prints error message or "Not found"
                print(f"-" * 30)
        elif choice == '7':
            # Launch the Watchlist Menu
            stock_watchlist.manage_watchlist(all_stocks)
        elif choice == '8':
            s_name = _select_stock(all_stocks)
            if s_name:
                stock_analysis.analyze_buy_sell_signals(all_stocks, s_name)
        elif choice == '9':
            s_name = _select_stock(all_stocks)
            if s_name:
                stock_portfolio.track_performance(all_stocks, s_name)
        elif choice == '10':
            print(f"Goodbye — {len(all_stocks)} stocks loaded.")
            break
        else:
            print("Invalid choice. Try again.")