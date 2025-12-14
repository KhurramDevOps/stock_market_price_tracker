# stock_portfolio.py

def track_performance(registry, stock_name):
    """
    Feature 6: Portfolio Performance Tracker.
    Calculates Profit/Loss based on user-selected Buy and Sell dates.
    """
    key = stock_name.strip().upper()
    
    # 1. Validation (Use your loaded data)
    if key not in registry:
        print(f"Error: Stock '{key}' not found.")
        return

    data = registry[key] # This is your list of dictionaries

    # 2. Get User Dates
    print(f"\n--- Simulation for {key} ---")
    buy_date = input("Enter BUY date (MM/DD/YYYY): ").strip()
    sell_date = input("Enter SELL date (MM/DD/YYYY): ").strip()

    # 3. Find Prices
    buy_price = None
    sell_price = None

    # Loop through data to find the specific dates
    for row in data:
        if row['date'] == buy_date:
            buy_price = row['close']
        if row['date'] == sell_date:
            sell_price = row['close']

    # 4. Check if dates exist
    if buy_price is None:
        print(f"Error: Buy date '{buy_date}' not found.")
        return
    if sell_price is None:
        print(f"Error: Sell date '{sell_date}' not found.")
        return

    # 5. Calculate Profit
    profit = sell_price - buy_price
    roi = (profit / buy_price) * 100

    # 6. Print Report
    print(f"\n{'='*40}")
    print(f"      PORTFOLIO PERFORMANCE: {key}")
    print(f"{'='*40}")
    print(f"Buy Date:     {buy_date:<12} | Price: ${buy_price:,.2f}")
    print(f"Sell Date:    {sell_date:<12} | Price: ${sell_price:,.2f}")
    print("-" * 40)
    
    # Visual feedback
    if profit >= 0:
        status = "PROFIT 🟢"
        sign = "+"
    else:
        status = "LOSS 🔴"
        sign = "" # Negative number has its own sign

    print(f"Result:       {status}")
    print(f"Net Change:   {sign}${profit:,.2f}")
    print(f"Return (ROI): {sign}{roi:.2f}%")
    print(f"{'='*40}\n")