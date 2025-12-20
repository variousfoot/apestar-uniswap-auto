#!/bin/bash
# Check current pool state using cast

# Configuration
RPC_URL="${RPC_URL:-https://arb1.arbitrum.io/rpc}"
POOL_ADDRESS="${POOL_ADDRESS:-0xC6962004f452bE9203591991D15f6b388e09E8D0}"

echo "=========================================="
echo "Uniswap V3 Pool Status Check"
echo "=========================================="
echo "Pool: $POOL_ADDRESS"
echo "RPC: $RPC_URL"
echo ""

# Get slot0 (current price info)
echo "📊 Pool State (slot0):"
SLOT0=$(cast call $POOL_ADDRESS "slot0()(uint160,int24,uint16,uint16,uint16,uint8,bool)" --rpc-url $RPC_URL)
echo "  Raw: $SLOT0"

# Parse slot0
SQRT_PRICE_X96=$(echo "$SLOT0" | head -1)
TICK=$(echo "$SLOT0" | sed -n '2p')

echo "  sqrtPriceX96: $SQRT_PRICE_X96"
echo "  Current Tick: $TICK"

# Get liquidity
echo ""
echo "💧 Liquidity:"
LIQUIDITY=$(cast call $POOL_ADDRESS "liquidity()(uint128)" --rpc-url $RPC_URL)
echo "  Total: $LIQUIDITY"

# Get tick spacing
echo ""
echo "📏 Tick Spacing:"
TICK_SPACING=$(cast call $POOL_ADDRESS "tickSpacing()(int24)" --rpc-url $RPC_URL)
echo "  Spacing: $TICK_SPACING"

# Get fee
echo ""
echo "💰 Fee:"
FEE=$(cast call $POOL_ADDRESS "fee()(uint24)" --rpc-url $RPC_URL)
echo "  Fee: $FEE ($(echo "scale=4; $FEE / 10000" | bc)%)"

# Get token addresses
echo ""
echo "🪙 Tokens:"
TOKEN0=$(cast call $POOL_ADDRESS "token0()(address)" --rpc-url $RPC_URL)
TOKEN1=$(cast call $POOL_ADDRESS "token1()(address)" --rpc-url $RPC_URL)
echo "  Token0: $TOKEN0"
echo "  Token1: $TOKEN1"

# Calculate approximate price
echo ""
echo "💵 Approximate Price Calculation:"
echo "  Use Python for accurate price: python3 -c \"print((($SQRT_PRICE_X96 / 2**96) ** 2) * 10**12)\""

echo ""
echo "=========================================="
echo "Done!"

