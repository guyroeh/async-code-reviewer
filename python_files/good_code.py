def calculate_item_total_price(item_price: float, tax_rate: float, discount: float) -> float:
    """
    Calculates the final price of an item by adding tax and subtracting the discount.
    """
    price_with_tax = item_price + (item_price * tax_rate)
    final_price = price_with_tax - discount
    return final_price