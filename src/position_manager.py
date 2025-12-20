"""
Uniswap V3 NonfungiblePositionManager interaction module
"""

import json
import time
from dataclasses import dataclass
from typing import Optional, List
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from eth_account.signers.local import LocalAccount

from .config import (
    POSITION_MANAGER_ABI_PATH, 
    ERC20_ABI_PATH, 
    Config,
    PROTOCOL_FEE_RECIPIENT,
    PROTOCOL_FEE_PERCENT,
)
from .utils import calculate_tick_range, align_tick_to_spacing


@dataclass
class NFTPosition:
    """NFT Position data from Position Manager"""
    token_id: int
    nonce: int
    operator: str
    token0: str
    token1: str
    fee: int
    tick_lower: int
    tick_upper: int
    liquidity: int
    fee_growth_inside_0_last: int
    fee_growth_inside_1_last: int
    tokens_owed_0: int
    tokens_owed_1: int


class PositionManager:
    """Interact with Uniswap V3 NonfungiblePositionManager"""
    
    MAX_UINT128 = 2**128 - 1
    
    def __init__(self, w3: Web3, config: Config, account: LocalAccount):
        self.w3 = w3
        self.config = config
        self.account = account
        self.address = Web3.to_checksum_address(config.position_manager_address)
        
        # Load ABIs
        with open(POSITION_MANAGER_ABI_PATH) as f:
            pm_abi = json.load(f)
        
        with open(ERC20_ABI_PATH) as f:
            self.erc20_abi = json.load(f)
        
        self.contract: Contract = w3.eth.contract(
            address=self.address,
            abi=pm_abi
        )
    
    def get_position(self, token_id: int) -> NFTPosition:
        """Get position data by token ID"""
        pos = self.contract.functions.positions(token_id).call()
        
        return NFTPosition(
            token_id=token_id,
            nonce=pos[0],
            operator=pos[1],
            token0=pos[2],
            token1=pos[3],
            fee=pos[4],
            tick_lower=pos[5],
            tick_upper=pos[6],
            liquidity=pos[7],
            fee_growth_inside_0_last=pos[8],
            fee_growth_inside_1_last=pos[9],
            tokens_owed_0=pos[10],
            tokens_owed_1=pos[11],
        )
    
    def get_positions_for_owner(self, owner: str) -> List[int]:
        """Get all position token IDs for an owner"""
        owner = Web3.to_checksum_address(owner)
        balance = self.contract.functions.balanceOf(owner).call()
        
        token_ids = []
        for i in range(balance):
            token_id = self.contract.functions.tokenOfOwnerByIndex(owner, i).call()
            token_ids.append(token_id)
        
        return token_ids
    
    def approve_token(self, token_address: str, amount: int) -> str:
        """Approve token spending for Position Manager"""
        token = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi
        )
        
        tx = token.functions.approve(
            self.address,
            amount
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
            'maxFeePerGas': self.w3.eth.gas_price,
            'maxPriorityFeePerGas': self.w3.to_wei(0.001, 'gwei'),
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return tx_hash.hex()
    
    def mint_position(
        self,
        token0: str,
        token1: str,
        fee: int,
        tick_lower: int,
        tick_upper: int,
        amount0_desired: int,
        amount1_desired: int,
        amount0_min: int = 0,
        amount1_min: int = 0,
        deadline: Optional[int] = None,
    ) -> tuple[str, int]:
        """
        Mint a new liquidity position
        
        Returns:
            (tx_hash, token_id)
        """
        if deadline is None:
            deadline = int(time.time()) + 600  # 10 minutes
        
        # Build mint params
        params = (
            Web3.to_checksum_address(token0),
            Web3.to_checksum_address(token1),
            fee,
            tick_lower,
            tick_upper,
            amount0_desired,
            amount1_desired,
            amount0_min,
            amount1_min,
            self.account.address,
            deadline,
        )
        
        # Estimate gas
        gas_estimate = self.contract.functions.mint(params).estimate_gas({
            'from': self.account.address,
        })
        
        tx = self.contract.functions.mint(params).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': int(gas_estimate * self.config.gas_limit_multiplier),
            'maxFeePerGas': self.w3.eth.gas_price,
            'maxPriorityFeePerGas': self.w3.to_wei(0.001, 'gwei'),
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        # Wait for receipt to get token ID
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Parse IncreaseLiquidity event to get token ID
        token_id = self._parse_token_id_from_receipt(receipt)
        
        return tx_hash.hex(), token_id
    
    def increase_liquidity(
        self,
        token_id: int,
        amount0_desired: int,
        amount1_desired: int,
        amount0_min: int = 0,
        amount1_min: int = 0,
        deadline: Optional[int] = None,
    ) -> str:
        """Increase liquidity in an existing position"""
        if deadline is None:
            deadline = int(time.time()) + 600
        
        params = (
            token_id,
            amount0_desired,
            amount1_desired,
            amount0_min,
            amount1_min,
            deadline,
        )
        
        gas_estimate = self.contract.functions.increaseLiquidity(params).estimate_gas({
            'from': self.account.address,
        })
        
        tx = self.contract.functions.increaseLiquidity(params).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': int(gas_estimate * self.config.gas_limit_multiplier),
            'maxFeePerGas': self.w3.eth.gas_price,
            'maxPriorityFeePerGas': self.w3.to_wei(0.001, 'gwei'),
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return tx_hash.hex()
    
    def decrease_liquidity(
        self,
        token_id: int,
        liquidity: int,
        amount0_min: int = 0,
        amount1_min: int = 0,
        deadline: Optional[int] = None,
    ) -> str:
        """Decrease liquidity in a position"""
        if deadline is None:
            deadline = int(time.time()) + 600
        
        params = (
            token_id,
            liquidity,
            amount0_min,
            amount1_min,
            deadline,
        )
        
        gas_estimate = self.contract.functions.decreaseLiquidity(params).estimate_gas({
            'from': self.account.address,
        })
        
        tx = self.contract.functions.decreaseLiquidity(params).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': int(gas_estimate * self.config.gas_limit_multiplier),
            'maxFeePerGas': self.w3.eth.gas_price,
            'maxPriorityFeePerGas': self.w3.to_wei(0.001, 'gwei'),
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return tx_hash.hex()
    
    def collect_fees(
        self,
        token_id: int,
        recipient: Optional[str] = None,
    ) -> dict:
        """
        Collect fees from a position.
        
        Returns:
            dict with transaction details and amounts
        """
        if recipient is None:
            recipient = self.account.address
        
        # Get balances before collection to calculate actual fees collected
        weth_before = self._get_token_balance(self.config.weth_address)
        usdc_before = self._get_token_balance(self.config.usdc_address)
        
        # Collect to bot wallet first
        params = (
            token_id,
            self.account.address,  # Collect to bot wallet
            self.MAX_UINT128,
            self.MAX_UINT128,
        )
        
        gas_estimate = self.contract.functions.collect(params).estimate_gas({
            'from': self.account.address,
        })
        
        tx = self.contract.functions.collect(params).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': int(gas_estimate * self.config.gas_limit_multiplier),
            'maxFeePerGas': self.w3.eth.gas_price,
            'maxPriorityFeePerGas': self.w3.to_wei(0.001, 'gwei'),
        })
        
        signed = self.account.sign_transaction(tx)
        collect_tx = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(collect_tx)
        
        # Calculate actual collected amounts
        weth_after = self._get_token_balance(self.config.weth_address)
        usdc_after = self._get_token_balance(self.config.usdc_address)
        
        weth_collected = weth_after - weth_before
        usdc_collected = usdc_after - usdc_before
        
        # Process fee distribution
        result = {
            'collect_tx': collect_tx.hex(),
            'protocol_fee_tx_0': None,
            'protocol_fee_tx_1': None,
            'fee_amount_0': 0,
            'fee_amount_1': 0,
            'user_amount_0': weth_collected,
            'user_amount_1': usdc_collected,
        }
        
        # Process WETH
        if weth_collected > 0:
            fee_amount_0 = (weth_collected * PROTOCOL_FEE_PERCENT) // 100
            if fee_amount_0 > 0:
                result['fee_amount_0'] = fee_amount_0
                result['user_amount_0'] = weth_collected - fee_amount_0
                result['protocol_fee_tx_0'] = self._transfer_token(
                    self.config.weth_address,
                    PROTOCOL_FEE_RECIPIENT,
                    fee_amount_0
                )
        
        # Process USDC
        if usdc_collected > 0:
            fee_amount_1 = (usdc_collected * PROTOCOL_FEE_PERCENT) // 100
            if fee_amount_1 > 0:
                result['fee_amount_1'] = fee_amount_1
                result['user_amount_1'] = usdc_collected - fee_amount_1
                result['protocol_fee_tx_1'] = self._transfer_token(
                    self.config.usdc_address,
                    PROTOCOL_FEE_RECIPIENT,
                    fee_amount_1
                )
        
        return result
    
    def _get_token_balance(self, token_address: str) -> int:
        """Get token balance for bot wallet"""
        token = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi
        )
        return token.functions.balanceOf(self.account.address).call()
    
    def _transfer_token(self, token_address: str, to: str, amount: int) -> str:
        """Transfer tokens to recipient"""
        token = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi
        )
        
        tx = token.functions.transfer(
            Web3.to_checksum_address(to),
            amount
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
            'maxFeePerGas': self.w3.eth.gas_price,
            'maxPriorityFeePerGas': self.w3.to_wei(0.001, 'gwei'),
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_hash.hex()
    
    def close_position(self, token_id: int) -> dict:
        """
        Close a position completely:
        1. Decrease liquidity to 0
        2. Collect all tokens and fees
        3. Burn the NFT
        
        Returns:
            dict with all transaction hashes and fee info
        """
        position = self.get_position(token_id)
        result = {
            'decrease_tx': None,
            'collect_result': None,
            'burn_tx': None,
        }
        
        # 1. Decrease liquidity if any
        if position.liquidity > 0:
            tx_hash = self.decrease_liquidity(token_id, position.liquidity)
            result['decrease_tx'] = tx_hash
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # 2. Collect all tokens
        collect_result = self.collect_fees(token_id)
        result['collect_result'] = collect_result
        
        # 3. Burn the NFT
        gas_estimate = self.contract.functions.burn(token_id).estimate_gas({
            'from': self.account.address,
        })
        
        tx = self.contract.functions.burn(token_id).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': int(gas_estimate * self.config.gas_limit_multiplier),
            'maxFeePerGas': self.w3.eth.gas_price,
            'maxPriorityFeePerGas': self.w3.to_wei(0.001, 'gwei'),
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        result['burn_tx'] = tx_hash.hex()
        
        return result
    
    def _parse_token_id_from_receipt(self, receipt) -> int:
        """Parse token ID from mint transaction receipt"""
        # Look for Transfer event (NFT minted)
        for log in receipt['logs']:
            # Transfer event topic
            if log['topics'][0].hex() == Web3.keccak(text='Transfer(address,address,uint256)').hex():
                if len(log['topics']) >= 4:
                    token_id = int(log['topics'][3].hex(), 16)
                    return token_id
        
        raise ValueError("Could not find token ID in transaction receipt")

