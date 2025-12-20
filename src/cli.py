"""
Apestar Uniswap Auto - CLI Interface
"""

import click
from rich.console import Console
from rich.panel import Panel

from .config import Config
from .bot import LiquidityBot, print_logo, print_footer
from .utils import eth_to_wei, usdc_to_raw, format_eth, format_usdc

console = Console()


def get_bot() -> LiquidityBot:
    """Initialize and return bot instance"""
    config = Config.from_env()
    config.validate()
    return LiquidityBot(config)


@click.group()
def cli():
    """
    🦍 APESTAR UNISWAP AUTO 🦍
    
    Automated concentrated liquidity provision on Uniswap V3
    """
    pass


@cli.command()
def status():
    """Show current pool and position status"""
    try:
        print_logo()
        bot = get_bot()
        bot.display_status()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--eth', type=float, required=True, help='Amount of ETH/WETH to provide')
@click.option('--usdc', type=float, required=True, help='Amount of USDC to provide')
@click.option('--range', 'tick_range', type=int, default=None, help='Custom tick range (overrides config)')
def create(eth: float, usdc: float, tick_range: int):
    """Create a new liquidity position"""
    try:
        print_logo()
        bot = get_bot()
        
        if tick_range:
            bot.config.tick_range = tick_range
        
        amount0 = eth_to_wei(eth)
        amount1 = usdc_to_raw(usdc)
        
        console.print(Panel(
            f"Creating position with:\n"
            f"  WETH: {format_eth(amount0)}\n"
            f"  USDC: {format_usdc(amount1)}\n"
            f"  Tick Range: ±{bot.config.tick_range}",
            title="🦍 Create Position",
            border_style="cyan"
        ))
        
        if click.confirm('Proceed?'):
            token_id = bot.create_position(amount0, amount1)
            console.print(f"[green]🦍 Position created! Token ID: {token_id}[/green]")
        else:
            console.print("[yellow]Cancelled[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def rebalance():
    """Rebalance active position to center around current price"""
    try:
        print_logo()
        bot = get_bot()
        
        if bot.state.active_position_id is None:
            console.print("[yellow]No active position to rebalance[/yellow]")
            return
        
        if click.confirm('🦍 Rebalance position?'):
            bot.rebalance()
        else:
            console.print("[yellow]Cancelled[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def collect():
    """Collect fees from active position"""
    try:
        print_logo()
        bot = get_bot()
        bot.collect_fees()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--token-id', type=int, required=True, help='Position token ID to close')
def close(token_id: int):
    """Close a position completely"""
    try:
        print_logo()
        bot = get_bot()
        
        position = bot.pm.get_position(token_id)
        console.print(Panel(
            f"Closing position #{token_id}:\n"
            f"  Liquidity: {position.liquidity:,}\n"
            f"  Pending Fees: {format_eth(position.tokens_owed_0)} / {format_usdc(position.tokens_owed_1)}",
            title="🦍 Close Position",
            border_style="cyan"
        ))
        
        if click.confirm('Close this position?'):
            result = bot.pm.close_position(token_id)
            console.print(f"[green]🦍 Position closed![/green]")
            print_footer()
        else:
            console.print("[yellow]Cancelled[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def run():
    """Run the bot continuously"""
    try:
        bot = get_bot()
        bot.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]🦍 Apestar stopped by user[/yellow]")
        print_footer()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def positions():
    """List all positions for this wallet"""
    try:
        print_logo()
        bot = get_bot()
        token_ids = bot.pm.get_positions_for_owner(bot.account.address)
        
        if not token_ids:
            console.print("[yellow]No positions found[/yellow]")
            return
        
        pool_state = bot.get_pool_state()
        
        for token_id in token_ids:
            pos = bot.pm.get_position(token_id)
            
            # Check if this is for our pool
            is_our_pool = (
                pos.token0.lower() == bot.pool.token0.lower() and
                pos.token1.lower() == bot.pool.token1.lower()
            )
            
            from .utils import tick_to_price, is_position_in_range
            
            in_range = is_position_in_range(pool_state.tick, pos.tick_lower, pos.tick_upper)
            
            console.print(Panel(
                f"Token ID: {token_id}\n"
                f"Pool Match: {'[green]Yes[/green]' if is_our_pool else '[red]No[/red]'}\n"
                f"Tick Range: {pos.tick_lower} → {pos.tick_upper}\n"
                f"Price Range: ${tick_to_price(pos.tick_lower):,.2f} → ${tick_to_price(pos.tick_upper):,.2f}\n"
                f"Liquidity: {pos.liquidity:,}\n"
                f"In Range: {'[green]Yes[/green]' if in_range else '[red]No[/red]'}\n"
                f"Uncollected: {format_eth(pos.tokens_owed_0)} / {format_usdc(pos.tokens_owed_1)}",
                title=f"🦍 Position #{token_id}",
                border_style="cyan"
            ))
        
        print_footer()
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == '__main__':
    cli()
