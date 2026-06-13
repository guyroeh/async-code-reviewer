def calculate_monthly_net_salary(annual_salary: float, tax_rate: float) -> float:
    """
    Calculates the net monthly salary by applying the tax rate to the annual salary
    and dividing by 12.
    """
    net_annual = annual_salary * (1 - tax_rate)
    monthly_take_home = net_annual / 12
    return monthly_take_home