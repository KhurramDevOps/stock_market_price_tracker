def generate_stock_summary(registry, stock_name):
    """
    Generates a 10-day statistical summary.
    Assumes CSV data is ordered Recent -> Old (Row 0 is newest).
    """
    key = stock_name.strip().upper()

    if key not in registry:
        print(f"Error: Stock '{key}' not found in registry.")
        return

    data = registry[key]
    if not data:
        print(f"Error: No data available for {key}.")
        return

    # Slice: First 10 rows (Recent -> Old)
    days_to_analyze = 10
    recent_data = data[:days_to_analyze]

    if not recent_data:
        print("Error: Not enough data to analyze.")
        return

    try:
        # Index 0 = Newest, Index -1 = Oldest in slice
        current_row = recent_data[0]   
        start_row = recent_data[-1]    

        current_close = current_row.get('close')
        start_close = start_row.get('close')

        # List Comprehensions for Max/Min
        valid_highs = [row['high'] for row in recent_data if row.get('high') is not None]
        valid_lows = [row['low'] for row in recent_data if row.get('low') is not None]
        valid_volumes = [row['volume'] for row in recent_data if row.get('volume') is not None]

        highest_price = max(valid_highs) if valid_highs else 0.0
        lowest_price = min(valid_lows) if valid_lows else 0.0
        
        if valid_volumes:
            avg_volume = sum(valid_volumes) / len(valid_volumes)
        else:
            avg_volume = 0

        # Calculations
        if start_close is not None and current_close is not None:
            price_change = current_close - start_close
            if start_close != 0:
                pct_change = (price_change / start_close) * 100
            else:
                pct_change = 0.0
        else:
            price_change = 0.0
            pct_change = 0.0

        # Output
        print(f"\n{'='*40}")
        print(f"       STOCK SUMMARY: {key}")
        print(f"{'='*40}")
        print(f"Period:            Last {len(recent_data)} Days")
        print(f"From Date:         {start_row.get('date')}")
        print(f"To Date:           {current_row.get('date')}")
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
        
    summary_data = [
        ["Metric", "Value"],
        ["Stock Name", key],
        ["Analysis Period", f"Last {len(recent_data)} Days"],
        ["From Date", start_row.get('date')],
        ["To Date", current_row.get('date')],
        ["Current Price", current_close],
        ["Price Change", price_change],
        ["Percent Change", f"{pct_change:.2f}%"],
        ["10-Day High", highest_price],
        ["10-Day Low", lowest_price],
        ["Avg Volume", int(avg_volume)]
    ]

    return summary_data

def _calculate_sma(prices, period):
    """
    Helper function: Calculates Simple Moving Average for a list of prices.
    Returns a list of SMA values matching the length of input prices.
    """
    sma_values = []
    for i in range(len(prices)):
        if i + 1 < period:
            # Not enough data yet (e.g., day 3 of a 10-day average)
            sma_values.append(None) 
        else:
            # Calculate average of the window
            window = prices[i - period + 1 : i + 1]
            avg = sum(window) / period
            sma_values.append(avg)
    return sma_values

def analyze_buy_sell_signals(registry, stock_name):
    """
    Identifies 'Golden Cross' (Buy) and 'Death Cross' (Sell) points.
    Includes CURRENT TREND status.
    """
    key = stock_name.strip().upper()
    if key not in registry:
        print(f"Error: Stock '{key}' not found.")
        return

    data = registry[key]
    # Reverse data so it is chronological (Oldest -> Newest)
    prices = [row['close'] for row in data][::-1]
    dates = [row['date'] for row in data][::-1]

    if len(prices) < 11:
        print("Not enough data to calculate signals.")
        return

    # Define Periods
    short_window = 5
    long_window = 10

    # Calculate SMAs
    short_sma = _calculate_sma(prices, short_window)
    long_sma = _calculate_sma(prices, long_window)

    print(f"\n{'='*60}")
    print(f"   BUY/SELL SIGNALS REPORT: {key}")
    print(f"{'='*60}")
    print(f"Strategy: SMA Cross (Short={short_window} vs Long={long_window})")
    print("-" * 60)
    print(f"{'Date':<12} | {'Signal':<10} | {'Price':<8} | {'Short SMA':<9} | {'Long SMA':<9}")
    print("-" * 60)

    found_any = False
    
    # 1. Historical Signals Loop
    for i in range(long_window, len(prices)):
        curr_short = short_sma[i]
        curr_long = long_sma[i]
        prev_short = short_sma[i-1]
        prev_long = long_sma[i-1]

        if None in [curr_short, curr_long, prev_short, prev_long]: continue

        date = dates[i]
        price = prices[i]
        
        # BUY SIGNAL
        if prev_short <= prev_long and curr_short > curr_long:
            print(f"{date:<12} | 🟢 BUY     | ${price:<7.2f} | {curr_short:<9.2f} | {curr_long:<9.2f}")
            found_any = True
            
        # SELL SIGNAL
        elif prev_short >= prev_long and curr_short < curr_long:
            print(f"{date:<12} | 🔴 SELL    | ${price:<7.2f} | {curr_short:<9.2f} | {curr_long:<9.2f}")
            found_any = True

    if not found_any:
        print("No crossover signals found in this period.")

    # --- 2. CURRENT STATUS (The 'What to do now' part) ---
    last_short = short_sma[-1]
    last_long = long_sma[-1]
    last_price = prices[-1]
    
    print("-" * 60)
    print("CURRENT TREND ANALYSIS (As of today):")
    print(f" > Short SMA ({short_window} days): ${last_short:.2f}")
    print(f" > Long SMA  ({long_window} days): ${last_long:.2f}")
    
    diff = last_short - last_long
    
    if last_short > last_long:
        status = "BULLISH (Upward Trend)"
        advice = "Hold or Buy. The trend is positive."
    else:
        status = "BEARISH (Downward Trend)"
        advice = "Sell or Stay Out. The trend is negative."
        
    print(f" > Status: {status}")
    print(f" > Gap:    {diff:+.2f} (Difference between lines)")
    print(f" > Advice: {advice}")
    print(f"{'='*60}\n")