# stock_query.py

def get_price_by_date(registry, stock_name, target_date):
    """
    [cite_start]Part 2: Query Stock Prices[cite: 16].
    Searches for a specific date in the stock data and returns the Close price.
    """
    # 1. Standardize inputs
    key = stock_name.strip().upper()
    target_date = target_date.strip()

    # 2. Check if stock exists
    if key not in registry:
        return f"Error: Stock '{key}' not found."

    data = registry[key]

    # 3. Search for the date
    # Your data is a list of dictionaries: [{'date': '12/12/2025', 'close': 278.28}, ...]
    for row in data:
        if row['date'] == target_date:
            price = row['close']
            if price is None:
                return "Price data is missing for this date."
            return price  # Return the found price immediately

    # 4. If loop finishes without finding the date
    return "Date not found."