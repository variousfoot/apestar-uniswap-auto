#!/bin/bash
# Calculate tick range for a position

RPC_URL="${RPC_URL:-https://arb1.arbitrum.io/rpc}"
POOL_ADDRESS="${POOL_ADDRESS:-0xC6962004f452bE9203591991D15f6b388e09E8D0}"
TICK_RANGE="${1:-300}"  # Default 300 tick spacings on each side

echo "=========================================="
echo "Calculate Tick Range"
echo "=========================================="
echo "Tick Range: ±$TICK_RANGE tick spacings"
echo ""

# Get current tick and tick spacing
SLOT0=$(cast call $POOL_ADDRESS "slot0()(uint160,int24,uint16,uint16,uint16,uint8,bool)" --rpc-url $RPC_URL)
CURRENT_TICK=$(echo "$SLOT0" | sed -n '2p')
TICK_SPACING=$(cast call $POOL_ADDRESS "tickSpacing()(int24)" --rpc-url $RPC_URL)

echo "Current Tick: $CURRENT_TICK"
echo "Tick Spacing: $TICK_SPACING"

# Calculate range using Python
python3 -c "
import math

current_tick = int('$CURRENT_TICK')
tick_spacing = int('$TICK_SPACING')
range_width = int('$TICK_RANGE')

# Align to tick spacing
aligned_tick = (current_tick // tick_spacing) * tick_spacing

# Calculate range
tick_lower = aligned_tick - (range_width * tick_spacing)
tick_upper = aligned_tick + (range_width * tick_spacing)

# Calculate prices
price_lower = (1.0001 ** tick_lower) * (10 ** 12)
price_upper = (1.0001 ** tick_upper) * (10 ** 12)
price_current = (1.0001 ** current_tick) * (10 ** 12)

print()
print('📊 Calculated Range:')
print(f'  Tick Lower: {tick_lower}')
print(f'  Tick Upper: {tick_upper}')
print()
print('💵 Price Range:')
print(f'  Lower: \${price_lower:,.2f}')
print(f'  Current: \${price_current:,.2f}')
print(f'  Upper: \${price_upper:,.2f}')
print()
print(f'  Range Width: {(price_upper/price_lower - 1) * 100:.2f}%')
"

echo ""
echo "=========================================="

