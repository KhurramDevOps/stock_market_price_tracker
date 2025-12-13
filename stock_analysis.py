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
    