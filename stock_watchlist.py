import os
import csv

WATCHLIST_FILE = "watchlist.csv"

def load_watchlist():
    """
    Reads the list of favorite stocks from a CSV file.
    Returns a list of strings, e.g., ['APPLE', 'TESLA']
    """
    favorites = []
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:  # Ensure row is not empty
                        favorites.append(row[0].strip().upper())
        except Exception:
            pass # Start with empty list if file is corrupt
    return favorites

def save_watchlist(favorites):
    """
    Saves the list of favorites back to the CSV file.
    """
    try:
        with open(WATCHLIST_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for stock in favorites:
                writer.writerow([stock])
    except Exception as e:
        print(f"Error saving watchlist: {e}")

def get_quick_info(registry, stock_name):
    """
    Generates the 'Quick Info' string with price, change, and EMOJIS.
    Logic: Compare Row 0 (Today) vs Row 1 (Yesterday).
    """
    key = stock_name.upper()
    
    # 1. Check if we have data for this favorite
    if key not in registry:
        return f"{key:<10} | (Data not loaded yet)"

    data = registry[key]
    if not data:
        return f"{key:<10} | (No data rows)"

    # 2. Get Today's Price
    recent_row = data[0]
    recent_price = recent_row.get('close')
    date_str = recent_row.get('date')

    if recent_price is None:
        return f"{key:<10} | (Price missing)"

    # 3. Calculate Change (Today - Yesterday)
    # We need at least 2 rows to calculate a change
    change_str = ""
    if len(data) > 1:
        prev_row = data[1]
        prev_price = prev_row.get('close')
        
        if prev_price is not None:
            diff = recent_price - prev_price
            
            # --- EMOJI LOGIC ---
            if diff > 0:
                emoji = "🟢 UP"
                sign = "+"
            elif diff < 0:
                emoji = "🔴 DOWN"
                sign = "" # Negative number already has '-'
            else:
                emoji = "⚪ FLAT"
                sign = ""

            change_str = f"| {emoji} {sign}{diff:.2f}"

    # 4. Format the final line
    # Example: APPLE      | $278.28 (12/12/2025) | 🔴 DOWN -4.82
    return f"{key:<10} | ${recent_price:<8.2f} ({date_str}) {change_str}"

def manage_watchlist(registry):
    """
    The Interactive Menu for the Watchlist.
    """
    while True:
        favorites = load_watchlist()
        
        print(f"\n{'='*50}")
        print("             MY WATCHLIST DASHBOARD")
        print(f"{'='*50}")
        
        if not favorites:
            print("(Your watchlist is empty)")
        else:
            # Loop through favorites and show live info
            for stock in favorites:
                info = get_quick_info(registry, stock)
                print(info)
        
        print("-" * 50)
        print("Options: (A)dd stock, (R)emove stock, (B)ack to Main Menu")
        choice = input("Enter choice: ").strip().lower()

        if choice == 'a':
            name = input("Enter stock name to ADD: ").strip().upper()
            
            # 1. NEW CHECK: Is the data loaded?
            if name not in registry:
                print(f"Error: Stock '{name}' is not loaded.") 
                print("Please upload the CSV for this stock first.")
                
            # 2. CHECK: Is it already in the list?
            elif name in favorites:
                print(f"'{name}' is already in your watchlist.")
                
            # 3. Success: Add it
            else:
                favorites.append(name)
                save_watchlist(favorites)
                print(f"Added {name}.")
                
        elif choice == 'r':
            name = input("Enter stock name to REMOVE: ").strip().upper()
            if name in favorites:
                favorites.remove(name)
                save_watchlist(favorites)
                print(f"Removed {name}.")
            else:
                print("Stock not found in watchlist.")
                
        elif choice == 'b':
            break
        else:
            print("Invalid choice.")