#!/bin/bash
# Get current ETH/USDC price from the pool

RPC_URL="${RPC_URL:-https://arb1.arbitrum.io/rpc}"
POOL_ADDRESS="${POOL_ADDRESS:-0xC6962004f452bE9203591991D15f6b388e09E8D0}"

# Get sqrtPriceX96 from slot0
SQRT_PRICE_X96=$(cast call $POOL_ADDRESS "slot0()(uint160,int24,uint16,uint16,uint16,uint8,bool)" --rpc-url $RPC_URL | head -1)

# Calculate price using Python (more accurate than bash)
python3 -c "
sqrt_price_x96 = int('$SQRT_PRICE_X96')
Q96 = 2 ** 96

# sqrt(price) = sqrtPriceX96 / Q96
sqrt_price = sqrt_price_x96 / Q96

# price = sqrt(price)^2
price = sqrt_price ** 2

# Adjust for decimals: ETH (18) vs USDC (6)
# price is token1/token0 = USDC/ETH
decimal_adjustment = 10 ** (18 - 6)
eth_price = price * decimal_adjustment

print(f'ETH/USDC Price: \${eth_price:,.2f}')
"

