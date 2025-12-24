#!/usr/bin/env python3
"""
Comprehensive Test Suite for FEEDOM Uniswap Auto
Tests all bot functionalities with fuzz testing
"""

import sys
import random
import math
sys.path.insert(0, '.')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Test counters
passed = 0
failed = 0
errors = []

def test(name):
    """Decorator for test functions"""
    def decorator(func):
        def wrapper():
            global passed, failed, errors
            try:
                func()
                console.print(f"  [green]✓[/green] {name}")
                passed += 1
                return True
            except AssertionError as e:
                console.print(f"  [red]✗[/red] {name}: {e}")
                failed += 1
                errors.append(f"{name}: {e}")
                return False
            except Exception as e:
                console.print(f"  [red]✗[/red] {name}: {type(e).__name__}: {e}")
                failed += 1
                errors.append(f"{name}: {type(e).__name__}: {e}")
                return False
        return wrapper
    return decorator


# ============================================
# 1. IMPORT TESTS
# ============================================
def test_imports():
    console.print("\n[bold cyan]1. Testing Imports[/bold cyan]")
    
    @test("Import src.config")
    def _():
        from src.config import Config, PROTOCOL_FEE_RECIPIENT, PROTOCOL_FEE_PERCENT
        assert PROTOCOL_FEE_RECIPIENT == "0x78d038a8B89Eb58D99ccE6a64f91aA212Afda636"
        assert PROTOCOL_FEE_PERCENT == 20
    _()
    
    @test("Import src.utils")
    def _():
        from src.utils import (
            tick_to_price, price_to_tick, sqrt_price_x96_to_price,
            calculate_tick_range, align_tick_to_spacing, format_eth, format_usdc
        )
    _()
    
    @test("Import src.pool")
    def _():
        from src.pool import UniswapV3Pool, PoolState, PositionInfo
    _()
    
    @test("Import src.position_manager")
    def _():
        from src.position_manager import PositionManager, NFTPosition
    _()
    
    @test("Import src.bot")
    def _():
        from src.bot import LiquidityBot, BotState, print_logo, FEEDOM_LOGO
        assert "UNISWAP AUTO" in FEEDOM_LOGO
        assert "🚀" in FEEDOM_LOGO
    _()
    
    @test("Import src.cli")
    def _():
        from src.cli import cli
    _()


# ============================================
# 2. UTILITY FUNCTION TESTS
# ============================================
def test_utils():
    console.print("\n[bold cyan]2. Testing Utility Functions[/bold cyan]")
    
    from src.utils import (
        tick_to_price, price_to_tick, sqrt_price_x96_to_price,
        price_to_sqrt_price_x96, tick_to_sqrt_price_x96,
        calculate_tick_range, align_tick_to_spacing,
        is_position_in_range, calculate_position_ratio,
        format_eth, format_usdc, wei_to_eth, eth_to_wei,
        usdc_to_raw, raw_to_usdc, Q96
    )
    
    @test("tick_to_price: tick 0 = price ~1")
    def _():
        price = tick_to_price(0, 18, 18)  # Same decimals
        assert 0.99 < price < 1.01, f"Expected ~1, got {price}"
    _()
    
    @test("tick_to_price: ETH/USDC at tick -196332")
    def _():
        price = tick_to_price(-196332)
        assert 2500 < price < 3500, f"Expected ~3000, got {price}"
    _()
    
    @test("price_to_tick: $3000 -> tick")
    def _():
        tick = price_to_tick(3000)
        assert -200000 < tick < -190000, f"Expected ~-196000, got {tick}"
    _()
    
    @test("price_to_tick and tick_to_price are inverses")
    def _():
        original_price = 2977.62
        tick = price_to_tick(original_price)
        recovered_price = tick_to_price(tick)
        # Allow 0.1% tolerance due to tick discretization
        assert abs(recovered_price - original_price) / original_price < 0.001
    _()
    
    @test("sqrt_price_x96_to_price: real pool value")
    def _():
        # Real value from Arbitrum ETH/USDC pool
        sqrt_price_x96 = 4323285490138582021239868
        price = sqrt_price_x96_to_price(sqrt_price_x96)
        assert 2500 < price < 3500, f"Expected ~2977, got {price}"
    _()
    
    @test("align_tick_to_spacing: spacing 10")
    def _():
        assert align_tick_to_spacing(195, 10) == 190
        assert align_tick_to_spacing(199, 10) == 190
        assert align_tick_to_spacing(200, 10) == 200
        assert align_tick_to_spacing(-195, 10) == -200
    _()
    
    @test("calculate_tick_range: centered range")
    def _():
        tick_lower, tick_upper = calculate_tick_range(-196332, 10, 300)
        assert tick_lower < -196332 < tick_upper
        assert (tick_upper - tick_lower) == 6000  # 300 * 10 * 2
    _()
    
    @test("is_position_in_range: boundary checks")
    def _():
        assert is_position_in_range(100, 50, 150) == True
        assert is_position_in_range(50, 50, 150) == True   # Lower inclusive
        assert is_position_in_range(150, 50, 150) == False  # Upper exclusive
        assert is_position_in_range(49, 50, 150) == False
        assert is_position_in_range(151, 50, 150) == False
    _()
    
    @test("calculate_position_ratio: extremes")
    def _():
        assert calculate_position_ratio(50, 50, 150) == 0.0   # At lower
        assert calculate_position_ratio(150, 50, 150) == 1.0  # At upper
        assert calculate_position_ratio(100, 50, 150) == 0.5  # Middle
        assert calculate_position_ratio(0, 50, 150) == 0.0    # Below
        assert calculate_position_ratio(200, 50, 150) == 1.0  # Above
    _()
    
    @test("format_eth: various amounts")
    def _():
        assert "1.000000 ETH" in format_eth(10**18)
        assert "0.500000 ETH" in format_eth(5 * 10**17)
        assert "0.000001 ETH" in format_eth(10**12)
    _()
    
    @test("format_usdc: various amounts")
    def _():
        assert "$100.00" in format_usdc(100 * 10**6)
        assert "$1,000.00" in format_usdc(1000 * 10**6)
    _()
    
    @test("wei/eth conversions")
    def _():
        assert wei_to_eth(10**18) == 1.0
        assert eth_to_wei(1.0) == 10**18
        assert eth_to_wei(wei_to_eth(123456789)) == 123456789
    _()
    
    @test("usdc conversions")
    def _():
        assert usdc_to_raw(100.0) == 100 * 10**6
        assert raw_to_usdc(100 * 10**6) == 100.0
    _()


# ============================================
# 3. FUZZ TESTING TICK MATH
# ============================================
def test_fuzz_tick_math():
    console.print("\n[bold cyan]3. Fuzz Testing Tick Math[/bold cyan]")
    
    from src.utils import (
        tick_to_price, price_to_tick, tick_to_sqrt_price_x96,
        sqrt_price_x96_to_price, align_tick_to_spacing, calculate_tick_range
    )
    
    @test("Fuzz: tick_to_price for 100 random ticks")
    def _():
        for _ in range(100):
            tick = random.randint(-500000, 500000)
            price = tick_to_price(tick, 18, 18)
            assert price > 0, f"Price must be positive for tick {tick}"
            assert not math.isnan(price), f"Price is NaN for tick {tick}"
            assert not math.isinf(price), f"Price is infinite for tick {tick}"
    _()
    
    @test("Fuzz: price_to_tick for 100 random prices")
    def _():
        for _ in range(100):
            price = random.uniform(0.0001, 1000000)
            tick = price_to_tick(price, 18, 18)
            assert isinstance(tick, int), f"Tick should be int for price {price}"
    _()
    
    @test("Fuzz: tick <-> price roundtrip 100 times")
    def _():
        for _ in range(100):
            original_tick = random.randint(-400000, -100000)  # ETH range
            price = tick_to_price(original_tick)
            recovered_tick = price_to_tick(price)
            # Should be within 1 tick due to rounding
            assert abs(recovered_tick - original_tick) <= 1
    _()
    
    @test("Fuzz: align_tick_to_spacing for various spacings")
    def _():
        spacings = [1, 10, 60, 200]
        for spacing in spacings:
            for _ in range(25):
                tick = random.randint(-500000, 500000)
                aligned = align_tick_to_spacing(tick, spacing)
                assert aligned % spacing == 0, f"Aligned tick {aligned} not divisible by {spacing}"
    _()
    
    @test("Fuzz: calculate_tick_range produces valid ranges")
    def _():
        for _ in range(50):
            current_tick = random.randint(-300000, -100000)
            spacing = random.choice([1, 10, 60, 200])
            width = random.randint(10, 500)
            
            lower, upper = calculate_tick_range(current_tick, spacing, width)
            
            assert lower < upper, f"Lower {lower} >= Upper {upper}"
            assert lower % spacing == 0, f"Lower {lower} not aligned to {spacing}"
            assert upper % spacing == 0, f"Upper {upper} not aligned to {spacing}"
    _()


# ============================================
# 4. FEE CALCULATION TESTS
# ============================================
def test_fee_calculations():
    console.print("\n[bold cyan]4. Testing Fee Calculations[/bold cyan]")
    
    from src.config import PROTOCOL_FEE_PERCENT
    
    @test("20% fee on 1 ETH")
    def _():
        collected = 10**18  # 1 ETH in wei
        fee = (collected * PROTOCOL_FEE_PERCENT) // 100
        user = collected - fee
        assert fee == 2 * 10**17  # 0.2 ETH
        assert user == 8 * 10**17  # 0.8 ETH
    _()
    
    @test("20% fee on $1000 USDC")
    def _():
        collected = 1000 * 10**6  # 1000 USDC
        fee = (collected * PROTOCOL_FEE_PERCENT) // 100
        user = collected - fee
        assert fee == 200 * 10**6  # $200
        assert user == 800 * 10**6  # $800
    _()
    
    @test("Fee on zero amount")
    def _():
        collected = 0
        fee = (collected * PROTOCOL_FEE_PERCENT) // 100
        assert fee == 0
    _()
    
    @test("Fuzz: fee + user always equals collected")
    def _():
        for _ in range(100):
            collected = random.randint(0, 10**20)
            fee = (collected * PROTOCOL_FEE_PERCENT) // 100
            user = collected - fee
            assert fee + user == collected
    _()
    
    @test("Fee percentage is always 20%")
    def _():
        for _ in range(50):
            collected = random.randint(1000, 10**20)
            fee = (collected * PROTOCOL_FEE_PERCENT) // 100
            actual_percent = (fee * 100) / collected
            assert 19.9 < actual_percent < 20.1  # Allow rounding
    _()


# ============================================
# 5. POOL INTERACTION TESTS (LIVE)
# ============================================
def test_pool_live():
    console.print("\n[bold cyan]5. Testing Live Pool Interaction[/bold cyan]")
    
    from web3 import Web3
    from src.pool import UniswapV3Pool
    
    RPC_URL = "https://arb1.arbitrum.io/rpc"
    POOL_ADDRESS = "0xC6962004f452bE9203591991D15f6b388e09E8D0"
    
    @test("Connect to Arbitrum RPC")
    def _():
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        assert w3.is_connected(), "Failed to connect to Arbitrum"
    _()
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    pool = UniswapV3Pool(w3, POOL_ADDRESS)
    
    @test("Get pool token0 (WETH)")
    def _():
        token0 = pool.token0
        assert token0.lower() == "0x82af49447d8a07e3bd95bd0d56f35241523fbab1".lower()
    _()
    
    @test("Get pool token1 (USDC)")
    def _():
        token1 = pool.token1
        assert token1.lower() == "0xaf88d065e77c8cc2239327c5edb3a432268e5831".lower()
    _()
    
    @test("Get pool fee (500 = 0.05%)")
    def _():
        fee = pool.fee
        assert fee == 500
    _()
    
    @test("Get pool tick spacing (10)")
    def _():
        spacing = pool.tick_spacing
        assert spacing == 10
    _()
    
    @test("Get pool state")
    def _():
        state = pool.get_state()
        assert state.sqrt_price_x96 > 0
        assert -300000 < state.tick < 0  # Reasonable ETH/USDC tick
        assert state.liquidity > 0
        assert state.fee == 500
        assert state.tick_spacing == 10
    _()
    
    @test("Pool price is reasonable ($1000-$10000)")
    def _():
        state = pool.get_state()
        price = state.price
        assert 1000 < price < 10000, f"Price {price} out of range"
    _()


# ============================================
# 6. LIQUIDITY MATH TESTS
# ============================================
def test_liquidity_math():
    console.print("\n[bold cyan]6. Testing Liquidity Math[/bold cyan]")
    
    from src.utils import (
        get_liquidity_for_amount0, get_liquidity_for_amount1,
        get_amount0_for_liquidity, get_amount1_for_liquidity,
        tick_to_sqrt_price_x96, calculate_liquidity_amounts
    )
    
    @test("Liquidity calculations are symmetric")
    def _():
        sqrt_a = tick_to_sqrt_price_x96(-200000)
        sqrt_b = tick_to_sqrt_price_x96(-190000)
        
        amount0 = 10**18  # 1 ETH
        liquidity = get_liquidity_for_amount0(sqrt_a, sqrt_b, amount0)
        recovered = get_amount0_for_liquidity(sqrt_a, sqrt_b, liquidity)
        
        # Allow 1% tolerance due to integer math
        assert abs(recovered - amount0) / amount0 < 0.01
    _()
    
    @test("Liquidity from amount1 (USDC)")
    def _():
        sqrt_a = tick_to_sqrt_price_x96(-200000)
        sqrt_b = tick_to_sqrt_price_x96(-190000)
        
        amount1 = 3000 * 10**6  # $3000 USDC
        liquidity = get_liquidity_for_amount1(sqrt_a, sqrt_b, amount1)
        recovered = get_amount1_for_liquidity(sqrt_a, sqrt_b, liquidity)
        
        assert abs(recovered - amount1) / amount1 < 0.01
    _()


# ============================================
# 7. CONFIG TESTS
# ============================================
def test_config():
    console.print("\n[bold cyan]7. Testing Configuration[/bold cyan]")
    
    import os
    from src.config import Config
    
    @test("Config loads defaults correctly")
    def _():
        # Temporarily clear env vars
        old_key = os.environ.get('PRIVATE_KEY')
        os.environ['PRIVATE_KEY'] = '0x' + '1' * 64  # Dummy key
        
        config = Config.from_env()
        
        assert config.tick_range == 300
        assert config.check_interval_seconds == 60
        assert config.rebalance_threshold_percent == 80
        assert config.slippage_tolerance_percent == 0.5
        
        # Restore
        if old_key:
            os.environ['PRIVATE_KEY'] = old_key
    _()
    
    @test("Config validation catches missing private key")
    def _():
        import os
        old_key = os.environ.get('PRIVATE_KEY')
        os.environ.pop('PRIVATE_KEY', None)
        
        try:
            config = Config.from_env()
            config.validate()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "PRIVATE_KEY" in str(e)
        finally:
            if old_key:
                os.environ['PRIVATE_KEY'] = old_key
    _()


# ============================================
# 8. CLI TESTS
# ============================================
def test_cli():
    console.print("\n[bold cyan]8. Testing CLI[/bold cyan]")
    
    from click.testing import CliRunner
    from src.cli import cli
    
    runner = CliRunner()
    
    @test("CLI --help works")
    def _():
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "FEEDOM" in result.output
    _()
    
    @test("CLI status --help")
    def _():
        result = runner.invoke(cli, ['status', '--help'])
        assert result.exit_code == 0
    _()
    
    @test("CLI create --help")
    def _():
        result = runner.invoke(cli, ['create', '--help'])
        assert result.exit_code == 0
        assert "--eth" in result.output
        assert "--usdc" in result.output
    _()
    
    @test("CLI positions --help")
    def _():
        result = runner.invoke(cli, ['positions', '--help'])
        assert result.exit_code == 0
    _()


# ============================================
# MAIN
# ============================================
def main():
    global passed, failed, errors
    
    console.print(Panel(
        "[bold]FEEDOM Uniswap Auto - Comprehensive Test Suite[/bold]\n\n"
        "Testing all bot functionalities with fuzz testing...",
        title="🚀 TEST SUITE 🚀",
        border_style="cyan"
    ))
    
    # Run all test groups
    test_imports()
    test_utils()
    test_fuzz_tick_math()
    test_fee_calculations()
    test_pool_live()
    test_liquidity_math()
    test_config()
    test_cli()
    
    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]TEST SUMMARY[/bold]")
    console.print("=" * 60)
    
    total = passed + failed
    console.print(f"  Total:  {total}")
    console.print(f"  [green]Passed: {passed}[/green]")
    console.print(f"  [red]Failed: {failed}[/red]")
    
    if errors:
        console.print("\n[red]Errors:[/red]")
        for error in errors:
            console.print(f"  - {error}")
    
    console.print()
    if failed == 0:
        console.print(Panel(
            f"[bold green]All {passed} tests passed![/bold green]\n\n"
            "🚀 FEEDOM Uniswap Auto is ready to use!",
            title="✅ SUCCESS",
            border_style="green"
        ))
        return 0
    else:
        console.print(Panel(
            f"[bold red]{failed} tests failed[/bold red]",
            title="❌ FAILURE",
            border_style="red"
        ))
        return 1


if __name__ == "__main__":
    sys.exit(main())

