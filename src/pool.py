"""
Uniswap V3 Pool interaction module
"""

import json
from dataclasses import dataclass
from typing import Optional
from web3 import Web3
from web3.contract import Contract

from .config import POOL_ABI_PATH, ERC20_ABI_PATH
from .utils import (
    sqrt_price_x96_to_price,
    tick_to_price,
    is_position_in_range,
    calculate_position_ratio,
)


@dataclass
class PoolState:
    """Current state of the pool"""
    sqrt_price_x96: int
    tick: int
    observation_index: int
    observation_cardinality: int
    observation_cardinality_next: int
    fee_protocol: int
    unlocked: bool
    liquidity: int
    fee: int
    tick_spacing: int
    token0: str
    token1: str
    
    @property
    def price(self) -> float:
        """Get current price (token1 per token0, e.g., USDC per ETH)"""
        return sqrt_price_x96_to_price(self.sqrt_price_x96)
    
    @property
    def price_readable(self) -> str:
        """Get human-readable price string"""
        return f"${self.price:,.2f}"


@dataclass
class PositionInfo:
    """Information about a liquidity position"""
    tick_lower: int
    tick_upper: int
    liquidity: int
    fee_growth_inside_0_last: int
    fee_growth_inside_1_last: int
    tokens_owed_0: int
    tokens_owed_1: int
    
    def is_in_range(self, current_tick: int) -> bool:
        """Check if position is in range"""
        return is_position_in_range(current_tick, self.tick_lower, self.tick_upper)
    
    def get_ratio(self, current_tick: int) -> float:
        """Get position ratio (0 = all token0, 1 = all token1)"""
        return calculate_position_ratio(current_tick, self.tick_lower, self.tick_upper)
    
    @property
    def price_lower(self) -> float:
        """Get lower price bound"""
        return tick_to_price(self.tick_lower)
    
    @property
    def price_upper(self) -> float:
        """Get upper price bound"""
        return tick_to_price(self.tick_upper)


class UniswapV3Pool:
    """Interact with a Uniswap V3 pool"""
    
    def __init__(self, w3: Web3, pool_address: str):
        self.w3 = w3
        self.pool_address = Web3.to_checksum_address(pool_address)
        
        # Load ABI
        with open(POOL_ABI_PATH) as f:
            pool_abi = json.load(f)
        
        with open(ERC20_ABI_PATH) as f:
            self.erc20_abi = json.load(f)
        
        self.contract: Contract = w3.eth.contract(
            address=self.pool_address,
            abi=pool_abi
        )
        
        # Cache token info
        self._token0: Optional[str] = None
        self._token1: Optional[str] = None
        self._fee: Optional[int] = None
        self._tick_spacing: Optional[int] = None
    
    @property
    def token0(self) -> str:
        """Get token0 address"""
        if self._token0 is None:
            self._token0 = self.contract.functions.token0().call()
        return self._token0
    
    @property
    def token1(self) -> str:
        """Get token1 address"""
        if self._token1 is None:
            self._token1 = self.contract.functions.token1().call()
        return self._token1
    
    @property
    def fee(self) -> int:
        """Get pool fee (in hundredths of a bip)"""
        if self._fee is None:
            self._fee = self.contract.functions.fee().call()
        return self._fee
    
    @property
    def tick_spacing(self) -> int:
        """Get pool tick spacing"""
        if self._tick_spacing is None:
            self._tick_spacing = self.contract.functions.tickSpacing().call()
        return self._tick_spacing
    
    def get_state(self) -> PoolState:
        """Get current pool state"""
        slot0 = self.contract.functions.slot0().call()
        liquidity = self.contract.functions.liquidity().call()
        
        return PoolState(
            sqrt_price_x96=slot0[0],
            tick=slot0[1],
            observation_index=slot0[2],
            observation_cardinality=slot0[3],
            observation_cardinality_next=slot0[4],
            fee_protocol=slot0[5],
            unlocked=slot0[6],
            liquidity=liquidity,
            fee=self.fee,
            tick_spacing=self.tick_spacing,
            token0=self.token0,
            token1=self.token1,
        )
    
    def get_position(self, owner: str, tick_lower: int, tick_upper: int) -> PositionInfo:
        """Get position info for an owner at specific tick range"""
        # Position key is keccak256(abi.encodePacked(owner, tickLower, tickUpper))
        position_key = Web3.solidity_keccak(
            ['address', 'int24', 'int24'],
            [Web3.to_checksum_address(owner), tick_lower, tick_upper]
        )
        
        position = self.contract.functions.positions(position_key).call()
        
        return PositionInfo(
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            liquidity=position[0],
            fee_growth_inside_0_last=position[1],
            fee_growth_inside_1_last=position[2],
            tokens_owed_0=position[3],
            tokens_owed_1=position[4],
        )
    
    def get_token_contract(self, token_address: str) -> Contract:
        """Get ERC20 contract for a token"""
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi
        )
    
    def get_token_balance(self, token_address: str, account: str) -> int:
        """Get token balance for an account"""
        token = self.get_token_contract(token_address)
        return token.functions.balanceOf(Web3.to_checksum_address(account)).call()
    
    def get_token_allowance(self, token_address: str, owner: str, spender: str) -> int:
        """Get token allowance"""
        token = self.get_token_contract(token_address)
        return token.functions.allowance(
            Web3.to_checksum_address(owner),
            Web3.to_checksum_address(spender)
        ).call()

