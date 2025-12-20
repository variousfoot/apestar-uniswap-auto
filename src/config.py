"""
Configuration management for Uniswap V3 Liquidity Bot
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Bot configuration loaded from environment variables"""
    
    # RPC
    rpc_url: str
    
    # Wallet
    private_key: str
    
    # Pool
    pool_address: str
    
    # Tokens (Arbitrum addresses)
    weth_address: str
    usdc_address: str
    
    # Position Manager
    position_manager_address: str
    
    # Bot Settings
    tick_range: int
    check_interval_seconds: int
    rebalance_threshold_percent: float
    slippage_tolerance_percent: float
    
    # Gas Settings
    max_gas_price_gwei: float
    gas_limit_multiplier: float
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls(
            rpc_url=os.getenv("RPC_URL", "https://arb1.arbitrum.io/rpc"),
            private_key=os.getenv("PRIVATE_KEY", ""),
            pool_address=os.getenv("POOL_ADDRESS", "0xC6962004f452bE9203591991D15f6b388e09E8D0"),
            weth_address=os.getenv("WETH_ADDRESS", "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"),
            usdc_address=os.getenv("USDC_ADDRESS", "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"),
            position_manager_address=os.getenv("POSITION_MANAGER_ADDRESS", "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"),
            tick_range=int(os.getenv("TICK_RANGE", "300")),
            check_interval_seconds=int(os.getenv("CHECK_INTERVAL_SECONDS", "60")),
            rebalance_threshold_percent=float(os.getenv("REBALANCE_THRESHOLD_PERCENT", "80")),
            slippage_tolerance_percent=float(os.getenv("SLIPPAGE_TOLERANCE_PERCENT", "0.5")),
            max_gas_price_gwei=float(os.getenv("MAX_GAS_PRICE_GWEI", "0.1")),
            gas_limit_multiplier=float(os.getenv("GAS_LIMIT_MULTIPLIER", "1.2")),
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.private_key or self.private_key == "your_private_key_here":
            raise ValueError("PRIVATE_KEY must be set in .env file")
        if not self.rpc_url:
            raise ValueError("RPC_URL must be set")
        return True


# Uniswap V3 Constants
Q96 = 2 ** 96
Q128 = 2 ** 128

# Arbitrum Chain ID
ARBITRUM_CHAIN_ID = 42161

# ABI Paths
ABI_DIR = Path(__file__).parent.parent / "abi"
POOL_ABI_PATH = ABI_DIR / "uniswap_v3_pool.json"
ERC20_ABI_PATH = ABI_DIR / "erc20.json"
POSITION_MANAGER_ABI_PATH = ABI_DIR / "nonfungible_position_manager.json"

# Fee configuration
PROTOCOL_FEE_RECIPIENT = "0x78d038a8B89Eb58D99ccE6a64f91aA212Afda636"
PROTOCOL_FEE_PERCENT = 20

