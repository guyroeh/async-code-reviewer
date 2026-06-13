def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculates the Euclidean distance between two 2D coordinate points.
    """
    x_diff_squared = (x2 - x1) ** 2
    y_diff_squared = (y2 - y1) ** 2
    distance = (x_diff_squared + y_diff_squared) ** 0.5
    return distance