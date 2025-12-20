"""
Utility functions for Uniswap V3 math and conversions
"""

import math
from decimal import Decimal, getcontext

# Set high precision for calculations
getcontext().prec = 78

Q96 = 2 ** 96
Q128 = 2 ** 128


def tick_to_price(tick: int, token0_decimals: int = 18, token1_decimals: int = 6) -> float:
    """
    Convert tick to human-readable price
    
    For ETH/USDC pool:
    - token0 = WETH (18 decimals)
    - token1 = USDC (6 decimals)
    - price = USDC per ETH
    """
    price = 1.0001 ** tick
    decimal_adjustment = 10 ** (token0_decimals - token1_decimals)
    return price * decimal_adjustment


def price_to_tick(price: float, token0_decimals: int = 18, token1_decimals: int = 6) -> int:
    """
    Convert price to tick
    
    Args:
        price: Price of token0 in terms of token1 (e.g., ETH price in USDC)
    """
    decimal_adjustment = 10 ** (token0_decimals - token1_decimals)
    adjusted_price = price / decimal_adjustment
    tick = math.floor(math.log(adjusted_price) / math.log(1.0001))
    return tick


def sqrt_price_x96_to_price(sqrt_price_x96: int, token0_decimals: int = 18, token1_decimals: int = 6) -> float:
    """
    Convert sqrtPriceX96 to human-readable price
    
    sqrtPriceX96 = sqrt(price) * 2^96
    price = (sqrtPriceX96 / 2^96)^2
    """
    sqrt_price = sqrt_price_x96 / Q96
    price = sqrt_price ** 2
    decimal_adjustment = 10 ** (token0_decimals - token1_decimals)
    return price * decimal_adjustment


def price_to_sqrt_price_x96(price: float, token0_decimals: int = 18, token1_decimals: int = 6) -> int:
    """Convert price to sqrtPriceX96"""
    decimal_adjustment = 10 ** (token0_decimals - token1_decimals)
    adjusted_price = price / decimal_adjustment
    sqrt_price = math.sqrt(adjusted_price)
    return int(sqrt_price * Q96)


def tick_to_sqrt_price_x96(tick: int) -> int:
    """Convert tick to sqrtPriceX96"""
    return int(math.sqrt(1.0001 ** tick) * Q96)


def get_tick_at_sqrt_ratio(sqrt_price_x96: int) -> int:
    """Get tick from sqrtPriceX96"""
    sqrt_price = sqrt_price_x96 / Q96
    price = sqrt_price ** 2
    tick = math.floor(math.log(price) / math.log(1.0001))
    return tick


def align_tick_to_spacing(tick: int, tick_spacing: int) -> int:
    """
    Align a tick to the nearest valid tick based on spacing
    
    Args:
        tick: The tick to align
        tick_spacing: The pool's tick spacing
        
    Returns:
        The aligned tick (rounded down)
    """
    return (tick // tick_spacing) * tick_spacing


def calculate_tick_range(current_tick: int, tick_spacing: int, range_width: int = 300) -> tuple[int, int]:
    """
    Calculate tick range centered around current tick
    
    Args:
        current_tick: Current pool tick
        tick_spacing: Pool tick spacing
        range_width: Number of tick spacings on each side (default 300)
        
    Returns:
        (tick_lower, tick_upper)
    """
    # Align current tick
    aligned_tick = align_tick_to_spacing(current_tick, tick_spacing)
    
    # Calculate range
    tick_lower = aligned_tick - (range_width * tick_spacing)
    tick_upper = aligned_tick + (range_width * tick_spacing)
    
    return tick_lower, tick_upper


def calculate_liquidity_amounts(
    sqrt_price_x96: int,
    tick_lower: int,
    tick_upper: int,
    amount0_desired: int,
    amount1_desired: int
) -> tuple[int, int, int]:
    """
    Calculate the amounts of token0 and token1 needed for a given liquidity amount
    
    Returns:
        (liquidity, amount0, amount1)
    """
    sqrt_price_a = tick_to_sqrt_price_x96(tick_lower)
    sqrt_price_b = tick_to_sqrt_price_x96(tick_upper)
    sqrt_price = sqrt_price_x96
    
    # Ensure price_a < price_b
    if sqrt_price_a > sqrt_price_b:
        sqrt_price_a, sqrt_price_b = sqrt_price_b, sqrt_price_a
    
    if sqrt_price <= sqrt_price_a:
        # Current price below range - only token0 needed
        liquidity = get_liquidity_for_amount0(sqrt_price_a, sqrt_price_b, amount0_desired)
        amount0 = get_amount0_for_liquidity(sqrt_price_a, sqrt_price_b, liquidity)
        amount1 = 0
    elif sqrt_price >= sqrt_price_b:
        # Current price above range - only token1 needed
        liquidity = get_liquidity_for_amount1(sqrt_price_a, sqrt_price_b, amount1_desired)
        amount0 = 0
        amount1 = get_amount1_for_liquidity(sqrt_price_a, sqrt_price_b, liquidity)
    else:
        # Current price in range - both tokens needed
        liquidity0 = get_liquidity_for_amount0(sqrt_price, sqrt_price_b, amount0_desired)
        liquidity1 = get_liquidity_for_amount1(sqrt_price_a, sqrt_price, amount1_desired)
        liquidity = min(liquidity0, liquidity1)
        
        amount0 = get_amount0_for_liquidity(sqrt_price, sqrt_price_b, liquidity)
        amount1 = get_amount1_for_liquidity(sqrt_price_a, sqrt_price, liquidity)
    
    return liquidity, amount0, amount1


def get_liquidity_for_amount0(sqrt_price_a: int, sqrt_price_b: int, amount0: int) -> int:
    """Calculate liquidity for a given amount of token0"""
    if sqrt_price_a > sqrt_price_b:
        sqrt_price_a, sqrt_price_b = sqrt_price_b, sqrt_price_a
    
    intermediate = (sqrt_price_a * sqrt_price_b) // Q96
    return (amount0 * intermediate) // (sqrt_price_b - sqrt_price_a)


def get_liquidity_for_amount1(sqrt_price_a: int, sqrt_price_b: int, amount1: int) -> int:
    """Calculate liquidity for a given amount of token1"""
    if sqrt_price_a > sqrt_price_b:
        sqrt_price_a, sqrt_price_b = sqrt_price_b, sqrt_price_a
    
    return (amount1 * Q96) // (sqrt_price_b - sqrt_price_a)


def get_amount0_for_liquidity(sqrt_price_a: int, sqrt_price_b: int, liquidity: int) -> int:
    """Calculate amount0 for a given liquidity"""
    if sqrt_price_a > sqrt_price_b:
        sqrt_price_a, sqrt_price_b = sqrt_price_b, sqrt_price_a
    
    return int(
        liquidity * Q96 * (sqrt_price_b - sqrt_price_a) // sqrt_price_b // sqrt_price_a
    )


def get_amount1_for_liquidity(sqrt_price_a: int, sqrt_price_b: int, liquidity: int) -> int:
    """Calculate amount1 for a given liquidity"""
    if sqrt_price_a > sqrt_price_b:
        sqrt_price_a, sqrt_price_b = sqrt_price_b, sqrt_price_a
    
    return int(liquidity * (sqrt_price_b - sqrt_price_a) // Q96)


def is_position_in_range(current_tick: int, tick_lower: int, tick_upper: int) -> bool:
    """Check if current tick is within position range"""
    return tick_lower <= current_tick < tick_upper


def calculate_position_ratio(
    current_tick: int,
    tick_lower: int,
    tick_upper: int
) -> float:
    """
    Calculate how much of the position range the current price has traversed
    
    Returns:
        0.0 = at lower tick (100% token0)
        1.0 = at upper tick (100% token1)
        0.5 = in middle (balanced)
    """
    if current_tick <= tick_lower:
        return 0.0
    if current_tick >= tick_upper:
        return 1.0
    return (current_tick - tick_lower) / (tick_upper - tick_lower)


def format_eth(wei: int) -> str:
    """Format wei to ETH with 6 decimal places"""
    return f"{wei / 10**18:.6f} ETH"


def format_usdc(amount: int) -> str:
    """Format USDC amount (6 decimals) to human readable"""
    return f"${amount / 10**6:,.2f}"


def wei_to_eth(wei: int) -> float:
    """Convert wei to ETH"""
    return wei / 10**18


def eth_to_wei(eth: float) -> int:
    """Convert ETH to wei"""
    return int(eth * 10**18)


def usdc_to_raw(usdc: float) -> int:
    """Convert USDC to raw amount (6 decimals)"""
    return int(usdc * 10**6)


def raw_to_usdc(raw: int) -> float:
    """Convert raw USDC amount to human readable"""
    return raw / 10**6

