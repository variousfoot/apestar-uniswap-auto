#!/bin/bash
# Check wallet balances

if [ -z "$1" ]; then
    echo "Usage: ./check_balance.sh <wallet_address>"
    exit 1
fi

WALLET=$1
RPC_URL="${RPC_URL:-https://arb1.arbitrum.io/rpc}"
WETH_ADDRESS="${WETH_ADDRESS:-0x82aF49447D8a07e3bd95BD0d56f35241523fBab1}"
USDC_ADDRESS="${USDC_ADDRESS:-0xaf88d065e77c8cC2239327C5EDb3A432268e5831}"

echo "=========================================="
echo "Wallet Balances"
echo "=========================================="
echo "Wallet: $WALLET"
echo ""

# ETH balance
ETH_WEI=$(cast balance $WALLET --rpc-url $RPC_URL)
ETH=$(cast from-wei $ETH_WEI)
echo "🔷 ETH (native): $ETH ETH"

# WETH balance
WETH_RAW=$(cast call $WETH_ADDRESS "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC_URL)
WETH=$(python3 -c "print(f'{int(\"$WETH_RAW\") / 10**18:.6f}')")
echo "🔶 WETH: $WETH WETH"

# USDC balance
USDC_RAW=$(cast call $USDC_ADDRESS "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC_URL)
USDC=$(python3 -c "print(f'{int(\"$USDC_RAW\") / 10**6:,.2f}')")
echo "💵 USDC: \$$USDC"

echo ""
echo "=========================================="

