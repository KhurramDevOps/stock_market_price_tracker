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
        print("\n[!] No stocks loaded. Please upload a CSV first.")
        return None

    print("\n--- Available Stocks ---")
    names = list(registry.keys())
    for i, name in enumerate(names, 1):
        # We can try to show row count if we want, but simple is clean
        print(f" {i}. {name}")
    print("------------------------")

    choice = input("Select stock (Name or Number): ").strip()
    
    # 1. Handle Number Input
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(names):
            return names[idx]
        else:
            print("❌ Invalid number.")
            return None
    
    # 2. Handle Text Input
    key = choice.upper()
    if key in registry:
        return key
    else:
        print(f"❌ Stock '{key}' not found.")
        return None

# ---------- Menu Display Function ----------
def print_main_menu():
    print("\n" + "="*60)
    print("       📈  STOCK MARKET PRICE TRACKER V1.0  📉")
    print("="*60)
    
    print(" [ DATA MANAGEMENT ]")
    print("  1) List Loaded Stocks")
    print("  2) Upload New Stock (CSV)")
    print("  3) Reload Stock from Disk")
    print("  4) Preview Raw Data")
    
    print("\n [ ANALYSIS & INSIGHTS ]")
    print("  5) Generate Stock Summary (Stats & Export)")
    print("  6) Query Price by Date")
    print("  7) My Watchlist Dashboard")
    
    print("\n [ PRO TOOLS ]")
    print("  8) Strategy Advisor (SMA Buy/Sell Signals)")
    print("  9) Portfolio Performance Simulator")
    
    print("\n [ SYSTEM ]")
    print("  10) Exit")
    print("="*60)

# ---------- Action Wrappers ----------

def list_stocks(registry):
    if not registry:
        print("\n[!] No stocks loaded.")
        return
    print("\n" + "-"*40)
    print(f"{'Stock Name':<15} | {'Rows Loaded'}")
    print("-" * 40)
    for name, data in registry.items():
        print(f"{name:<15} | {len(data)}")
    print("-" * 40)

def upload_stock_action(registry):
    print("\n--- Upload New Stock ---")
    path = input("Enter full path to CSV (or 'cancel'): ").strip()
    if path.lower() == 'cancel':
        return

    # Validate
    valid, meta = stock_loader.validate_csv_structure(path)
    if not valid:
        print(f"❌ Validation failed: {meta.get('error')}")
        return

    # Check Duplicates
    stock_name = stock_loader.extract_stock_name_from_path(path)
    key = stock_name.upper()

    if key in registry:
        while True:
            ans = input(f"⚠️  Stock '{stock_name}' exists. (R)eplace / (K)eep / (C)ancel? ").lower()
            if ans == 'r': break
            elif ans == 'k': return
            elif ans == 'c': return

    # Perform Upload
    print(f"Uploading {stock_name}...")
    new_path = stock_loader.save_uploaded_file(path)
    
    if new_path:
        try:
            rows = stock_loader.read_csv_to_list_of_dicts(new_path)
            stock_loader.add_stock_to_registry(registry, stock_name, rows, replace=True)
            print(f"✅ Successfully loaded {stock_name} ({len(rows)} rows)")
        except Exception as e:
            print(f"❌ Error reading file: {e}")

def reload_stock_action(registry):
    if not registry:
        print("No stocks to reload.")
        return
    
    name = _select_stock(registry)
    if not name: return

    # Check data folder
    data_dir = "data"
    filename = None
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
            print(f"✅ Reloaded {name} from disk.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"❌ File for {name} not found in 'data/' folder.")

def preview_stock_action(registry):
    name = _select_stock(registry)
    if not name: return

    data = registry[name]
    n = min(5, len(data))
    print(f"\nFirst {n} rows for {name}:")
    print("-" * 65)
    print(f"{'Date':<12} | {'Open':<8} | {'High':<8} | {'Low':<8} | {'Close':<8} | {'Volume'}")
    print("-" * 65)
    for row in data[:n]:
        d = row.get('date', '')
        o = row.get('open', '')
        h = row.get('high', '')
        l = row.get('low', '')
        c = row.get('close', '')
        v = row.get('volume', '')
        print(f"{d:<12} | {o:<8} | {h:<8} | {l:<8} | {c:<8} | {v}")
    print("-" * 65)

# ---------- Main Execution ----------

if __name__ == "__main__":
    all_stocks = {}

    # 1. Auto-Load existing data
    data_dir = "data/"
    if os.path.exists(data_dir):
        print("Initializing System...")
        for filename in os.listdir(data_dir):
            path = os.path.join(data_dir, filename)
            if stock_loader.is_csv_file(path):
                try:
                    rows = stock_loader.read_csv_to_list_of_dicts(path)
                    s_name = stock_loader.extract_stock_name_from_path(path)
                    stock_loader.add_stock_to_registry(all_stocks, s_name, rows)
                    # print(f" [OK] Loaded {s_name}") # Optional: keep startup silent or verbose
                except Exception:
                    pass
    else:
        os.makedirs(data_dir, exist_ok=True)

    # 2. Main Loop
    while True:
        print_main_menu()
        choice = input("Enter choice (1-10): ").strip()

        if choice == '1':
            list_stocks(all_stocks)
        
        elif choice == '2':
            upload_stock_action(all_stocks)
        
        elif choice == '3':
            reload_stock_action(all_stocks)
        
        elif choice == '4':
            preview_stock_action(all_stocks)
        
        elif choice == '5':
            # Summary & Export
            s_name = _select_stock(all_stocks)
            if s_name:
                data_to_save = stock_analysis.generate_stock_summary(all_stocks, s_name)
                if data_to_save:
                    save_ans = input("💾 Save this summary to CSV? (y/n): ").strip().lower()
                    if save_ans == 'y':
                        fname = f"Summary_{s_name}.csv"
                        path = stock_loader.save_csv_file(fname, data_to_save)
                        if path: print(f"✅ Saved to: {path}")

        elif choice == '6':
            # Query Date
            s_name = _select_stock(all_stocks)
            if s_name:
                date_in = input("Enter date (MM/DD/YYYY): ").strip()
                res = stock_query.get_price_by_date(all_stocks, s_name, date_in)
                print("-" * 30)
                if isinstance(res, float):
                    print(f"📅 Date:  {date_in}")
                    print(f"💵 Price: ${res:,.2f}")
                else:
                    print(f"⚠️  {res}")
                print("-" * 30)

        elif choice == '7':
            # Watchlist
            stock_watchlist.manage_watchlist(all_stocks)

        elif choice == '8':
            # Strategy Advisor
            s_name = _select_stock(all_stocks)
            if s_name:
                stock_analysis.analyze_buy_sell_signals(all_stocks, s_name)

        elif choice == '9':
            # Portfolio Simulator
            s_name = _select_stock(all_stocks)
            if s_name:
                stock_portfolio.track_performance(all_stocks, s_name)

        elif choice == '10':
            print("\n👋 Exiting Program. Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")