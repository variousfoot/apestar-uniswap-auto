"""
FEEDOM - Uniswap Auto Bot Engine
"""

import time
from dataclasses import dataclass
from typing import Optional, List
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .config import Config
from .pool import UniswapV3Pool, PoolState
from .position_manager import PositionManager, NFTPosition
from .utils import (
    calculate_tick_range,
    align_tick_to_spacing,
    tick_to_price,
    format_eth,
    format_usdc,
    is_position_in_range,
    calculate_position_ratio,
)


console = Console()

# FEEDOM ASCII Art Logo
FEEDOM_LOGO = """
[bold cyan]
    ╔════════════════════════════════════════════════════════════════════╗
    ║       ███████╗███████╗███████╗██████╗  ██████╗ ███╗   ███╗         ║
    ║       ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗████╗ ████║         ║
    ║       █████╗  █████╗  █████╗  ██║  ██║██║   ██║██╔████╔██║         ║
    ║       ██╔══╝  ██╔══╝  ██╔══╝  ██║  ██║██║   ██║██║╚██╔╝██║         ║
    ║       ██║     ███████╗███████╗██████╔╝╚██████╔╝██║ ╚═╝ ██║         ║
    ║       ╚═╝     ╚══════╝╚══════╝╚═════╝  ╚═════╝ ╚═╝     ╚═╝         ║
    ║                                                                    ║
    ║                    [bold yellow]🚀 UNISWAP AUTO 🚀[/bold yellow][bold cyan]                          ║
    ║          Automated Concentrated Liquidity on Arbitrum              ║
    ║                       [bold magenta]feedom.tech[/bold magenta][bold cyan]                               ║
    ╚════════════════════════════════════════════════════════════════════╝
[/bold cyan]"""


def print_logo():
    """Print the FEEDOM logo"""
    console.print(FEEDOM_LOGO)


def print_footer():
    """Print FEEDOM footer"""
    console.print("[dim]🚀 Powered by FEEDOM | feedom.tech[/dim]")


@dataclass
class BotState:
    """Current state of the bot"""
    active_position_id: Optional[int] = None
    tick_lower: Optional[int] = None
    tick_upper: Optional[int] = None
    last_check_time: float = 0
    rebalance_count: int = 0


class LiquidityBot:
    """
    FEEDOM Uniswap Auto - Automated Concentrated Liquidity Bot
    
    Strategy:
    - Maintains a position centered around current price
    - Uses configurable tick range (default: 300 tick spacings)
    - Rebalances when price moves beyond threshold
    - Collects fees periodically
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Setup Web3
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {config.rpc_url}")
        
        # Setup account
        self.account: LocalAccount = Account.from_key(config.private_key)
        console.print(f"[green]Wallet:[/green] {self.account.address}")
        
        # Setup pool and position manager
        self.pool = UniswapV3Pool(self.w3, config.pool_address)
        self.pm = PositionManager(self.w3, config, self.account)
        
        # Bot state
        self.state = BotState()
        
        # Load existing positions
        self._load_existing_positions()
    
    def _load_existing_positions(self):
        """Load any existing positions for this wallet"""
        token_ids = self.pm.get_positions_for_owner(self.account.address)
        
        if token_ids:
            console.print(f"[yellow]Found {len(token_ids)} existing position(s)[/yellow]")
            
            # Find positions for our pool
            for token_id in token_ids:
                pos = self.pm.get_position(token_id)
                if (pos.token0.lower() == self.pool.token0.lower() and 
                    pos.token1.lower() == self.pool.token1.lower() and
                    pos.fee == self.pool.fee):
                    
                    if pos.liquidity > 0:
                        self.state.active_position_id = token_id
                        self.state.tick_lower = pos.tick_lower
                        self.state.tick_upper = pos.tick_upper
                        console.print(f"[green]Using existing position #{token_id}[/green]")
                        break
    
    def get_pool_state(self) -> PoolState:
        """Get current pool state"""
        return self.pool.get_state()
    
    def get_active_position(self) -> Optional[NFTPosition]:
        """Get active position if exists"""
        if self.state.active_position_id is None:
            return None
        return self.pm.get_position(self.state.active_position_id)
    
    def display_status(self):
        """Display current bot status"""
        pool_state = self.get_pool_state()
        
        # Pool info table
        pool_table = Table(title="🚀 Pool Status", show_header=False)
        pool_table.add_column("Property", style="cyan")
        pool_table.add_column("Value", style="green")
        
        pool_table.add_row("Pool", self.config.pool_address)
        pool_table.add_row("Current Price", pool_state.price_readable)
        pool_table.add_row("Current Tick", str(pool_state.tick))
        pool_table.add_row("Tick Spacing", str(pool_state.tick_spacing))
        pool_table.add_row("Fee", f"{pool_state.fee / 10000}%")
        pool_table.add_row("Liquidity", f"{pool_state.liquidity:,}")
        
        console.print(pool_table)
        
        # Position info
        position = self.get_active_position()
        if position:
            pos_table = Table(title="🚀 Active Position", show_header=False)
            pos_table.add_column("Property", style="cyan")
            pos_table.add_column("Value", style="green")
            
            in_range = is_position_in_range(pool_state.tick, position.tick_lower, position.tick_upper)
            ratio = calculate_position_ratio(pool_state.tick, position.tick_lower, position.tick_upper)
            
            pos_table.add_row("Token ID", str(position.token_id))
            pos_table.add_row("Tick Range", f"{position.tick_lower} → {position.tick_upper}")
            pos_table.add_row("Price Range", f"${tick_to_price(position.tick_lower):,.2f} → ${tick_to_price(position.tick_upper):,.2f}")
            pos_table.add_row("Liquidity", f"{position.liquidity:,}")
            pos_table.add_row("In Range", "[green]Yes[/green]" if in_range else "[red]No[/red]")
            pos_table.add_row("Position Ratio", f"{ratio * 100:.1f}% (0%=ETH, 100%=USDC)")
            pos_table.add_row("Uncollected Fees", f"{format_eth(position.tokens_owed_0)} / {format_usdc(position.tokens_owed_1)}")
            
            console.print(pos_table)
        else:
            console.print("[yellow]No active position[/yellow]")
        
        # Wallet balances
        weth_balance = self.pool.get_token_balance(self.config.weth_address, self.account.address)
        usdc_balance = self.pool.get_token_balance(self.config.usdc_address, self.account.address)
        eth_balance = self.w3.eth.get_balance(self.account.address)
        
        balance_table = Table(title="🚀 Wallet Balances", show_header=False)
        balance_table.add_column("Token", style="cyan")
        balance_table.add_column("Balance", style="green")
        
        balance_table.add_row("ETH (native)", format_eth(eth_balance))
        balance_table.add_row("WETH", format_eth(weth_balance))
        balance_table.add_row("USDC", format_usdc(usdc_balance))
        
        console.print(balance_table)
        print_footer()
    
    def needs_rebalance(self) -> bool:
        """Check if position needs rebalancing"""
        if self.state.active_position_id is None:
            return False
        
        pool_state = self.get_pool_state()
        position = self.get_active_position()
        
        if position is None or position.liquidity == 0:
            return False
        
        # Check if out of range
        if not is_position_in_range(pool_state.tick, position.tick_lower, position.tick_upper):
            return True
        
        # Check if position ratio exceeds threshold
        ratio = calculate_position_ratio(pool_state.tick, position.tick_lower, position.tick_upper)
        threshold = self.config.rebalance_threshold_percent / 100
        
        if ratio < (1 - threshold) / 2 or ratio > (1 + threshold) / 2:
            return True
        
        return False
    
    def calculate_new_range(self) -> tuple[int, int]:
        """Calculate new tick range centered on current price"""
        pool_state = self.get_pool_state()
        
        return calculate_tick_range(
            pool_state.tick,
            pool_state.tick_spacing,
            self.config.tick_range
        )
    
    def ensure_approvals(self, amount0: int, amount1: int):
        """Ensure token approvals for Position Manager"""
        # Check WETH allowance
        weth_allowance = self.pool.get_token_allowance(
            self.config.weth_address,
            self.account.address,
            self.config.position_manager_address
        )
        
        if weth_allowance < amount0:
            console.print("[yellow]Approving WETH...[/yellow]")
            tx_hash = self.pm.approve_token(self.config.weth_address, 2**256 - 1)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            console.print(f"[green]WETH approved: {tx_hash}[/green]")
        
        # Check USDC allowance
        usdc_allowance = self.pool.get_token_allowance(
            self.config.usdc_address,
            self.account.address,
            self.config.position_manager_address
        )
        
        if usdc_allowance < amount1:
            console.print("[yellow]Approving USDC...[/yellow]")
            tx_hash = self.pm.approve_token(self.config.usdc_address, 2**256 - 1)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            console.print(f"[green]USDC approved: {tx_hash}[/green]")
    
    def create_position(
        self,
        amount0: int,
        amount1: int,
        tick_lower: Optional[int] = None,
        tick_upper: Optional[int] = None,
    ) -> int:
        """
        Create a new liquidity position
        
        Args:
            amount0: Amount of WETH (in wei)
            amount1: Amount of USDC (in 6 decimals)
            tick_lower: Lower tick (auto-calculated if None)
            tick_upper: Upper tick (auto-calculated if None)
            
        Returns:
            Token ID of the new position
        """
        pool_state = self.get_pool_state()
        
        # Calculate tick range if not provided
        if tick_lower is None or tick_upper is None:
            tick_lower, tick_upper = self.calculate_new_range()
        
        console.print(Panel(
            f"Creating position:\n"
            f"  Range: {tick_lower} → {tick_upper}\n"
            f"  Price: ${tick_to_price(tick_lower):,.2f} → ${tick_to_price(tick_upper):,.2f}\n"
            f"  WETH: {format_eth(amount0)}\n"
            f"  USDC: {format_usdc(amount1)}",
            title="🚀 New Position",
            border_style="cyan"
        ))
        
        # Ensure approvals
        self.ensure_approvals(amount0, amount1)
        
        # Calculate minimum amounts with slippage
        slippage = self.config.slippage_tolerance_percent / 100
        amount0_min = int(amount0 * (1 - slippage))
        amount1_min = int(amount1 * (1 - slippage))
        
        # Mint position
        tx_hash, token_id = self.pm.mint_position(
            token0=self.pool.token0,
            token1=self.pool.token1,
            fee=self.pool.fee,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            amount0_desired=amount0,
            amount1_desired=amount1,
            amount0_min=amount0_min,
            amount1_min=amount1_min,
        )
        
        console.print(f"[green]Position created! Token ID: {token_id}[/green]")
        console.print(f"[dim]TX: {tx_hash}[/dim]")
        print_footer()
        
        # Update state
        self.state.active_position_id = token_id
        self.state.tick_lower = tick_lower
        self.state.tick_upper = tick_upper
        
        return token_id
    
    def rebalance(self):
        """Rebalance the position to center around current price"""
        if self.state.active_position_id is None:
            console.print("[yellow]No position to rebalance[/yellow]")
            return
        
        console.print("[yellow]🚀 Starting rebalance...[/yellow]")
        
        position = self.get_active_position()
        
        # 1. Close existing position
        console.print("Closing existing position...")
        close_result = self.pm.close_position(self.state.active_position_id)
        
        console.print("[green]Position closed[/green]")
        
        # 2. Get new balances
        weth_balance = self.pool.get_token_balance(self.config.weth_address, self.account.address)
        usdc_balance = self.pool.get_token_balance(self.config.usdc_address, self.account.address)
        
        console.print(f"Available: {format_eth(weth_balance)} WETH, {format_usdc(usdc_balance)} USDC")
        
        # 3. Create new position with available balance
        if weth_balance > 0 or usdc_balance > 0:
            self.create_position(weth_balance, usdc_balance)
            self.state.rebalance_count += 1
            console.print(f"[green]🚀 Rebalance complete! (Total: {self.state.rebalance_count})[/green]")
        else:
            console.print("[red]No tokens available for new position[/red]")
            self.state.active_position_id = None
    
    def collect_fees(self):
        """Collect fees from active position"""
        if self.state.active_position_id is None:
            console.print("[yellow]No position to collect fees from[/yellow]")
            return
        
        position = self.get_active_position()
        if position.tokens_owed_0 == 0 and position.tokens_owed_1 == 0:
            console.print("[dim]No fees to collect[/dim]")
            return
        
        console.print(f"🚀 Collecting {format_eth(position.tokens_owed_0)} WETH, {format_usdc(position.tokens_owed_1)} USDC")
        
        result = self.pm.collect_fees(self.state.active_position_id)
        
        console.print(f"[green]Fees collected! TX: {result['collect_tx']}[/green]")
        console.print(f"[green]Received: {format_eth(result['user_amount_0'])} WETH, {format_usdc(result['user_amount_1'])} USDC[/green]")
        print_footer()
    
    def run_once(self):
        """Run one iteration of the bot"""
        console.print("\n" + "=" * 60)
        console.print(f"[bold cyan]🚀 FEEDOM Check @ {time.strftime('%Y-%m-%d %H:%M:%S')}[/bold cyan]")
        console.print("=" * 60)
        
        self.display_status()
        
        # Check if rebalance needed
        if self.needs_rebalance():
            console.print("[yellow]Position out of optimal range - rebalancing...[/yellow]")
            self.rebalance()
        else:
            console.print("[green]🚀 Position in optimal range[/green]")
        
        self.state.last_check_time = time.time()
    
    def run(self):
        """Run the bot continuously"""
        print_logo()
        
        console.print(Panel(
            f"[bold]ETH/USDC Liquidity Automation[/bold]\n\n"
            f"Pool: {self.config.pool_address}\n"
            f"Tick Range: ±{self.config.tick_range} spacing\n"
            f"Check Interval: {self.config.check_interval_seconds}s\n"
            f"Rebalance Threshold: {self.config.rebalance_threshold_percent}%",
            title="🚀 [bold cyan]FEEDOM UNISWAP AUTO[/bold cyan] 🚀",
            border_style="cyan",
            subtitle="[dim]Automated Concentrated Liquidity[/dim]"
        ))
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            
            console.print(f"\n[dim]🚀 Sleeping {self.config.check_interval_seconds}s...[/dim]")
            time.sleep(self.config.check_interval_seconds)
