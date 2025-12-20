# 🦍 APESTAR UNISWAP AUTO

```
 █████╗ ██████╗ ███████╗███████╗████████╗ █████╗ ██████╗ 
██╔══██╗██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗
███████║██████╔╝█████╗  ███████╗   ██║   ███████║██████╔╝
██╔══██║██╔═══╝ ██╔══╝  ╚════██║   ██║   ██╔══██║██╔══██╗
██║  ██║██║     ███████╗███████║   ██║   ██║  ██║██║  ██║
╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝
                    UNISWAP AUTO
        Automated Concentrated Liquidity on Arbitrum
```

An open-source bot by **Apestar** for automated concentrated liquidity provision on Uniswap V3 ETH/USDC pool on Arbitrum.

## ✨ Features

- 🎯 **Concentrated Liquidity**: Provides liquidity in a ±300 tick spacing range (configurable)
- 🔄 **Auto-Rebalancing**: Automatically rebalances when price moves out of optimal range
- 💰 **Fee Collection**: Collects accumulated trading fees
- 📊 **Position Monitoring**: Real-time status display of pool and positions
- 🔧 **Foundry Integration**: Uses `cast` for quick on-chain queries

## 🦍 Pool Information

- **Network**: Arbitrum One
- **Pool Address**: `0xC6962004f452bE9203591991D15f6b388e09E8D0`
- **Token0**: WETH (`0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`)
- **Token1**: USDC (`0xaf88d065e77c8cC2239327C5EDb3A432268e5831`)
- **Fee Tier**: 0.05% (500)

## 📋 Prerequisites

- Python 3.10+
- [Foundry](https://getfoundry.sh/) (for `cast` scripts)

## 🚀 Installation

1. **Clone the repository**:
```bash
git clone https://github.com/variousfoot/apestar-uniswap-auto.git
cd apestar-uniswap-auto
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Foundry** (if not already installed):
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

4. **Configure environment**:
```bash
cp env.example .env
# Edit .env with your settings
```

## ⚙️ Configuration

Edit the `.env` file with your settings:

```env
# RPC URL (Arbitrum)
RPC_URL=https://arb1.arbitrum.io/rpc

# Your private key (NEVER share this!)
PRIVATE_KEY=your_private_key_here

# Bot settings
TICK_RANGE=300                    # Number of tick spacings on each side
CHECK_INTERVAL_SECONDS=60         # How often to check position
REBALANCE_THRESHOLD_PERCENT=80    # Rebalance when 80% through range
SLIPPAGE_TOLERANCE_PERCENT=0.5    # Max slippage for transactions
```

## 🦍 Usage

### CLI Commands

```bash
# Show current status
python apestar.py status

# Create a new position
python apestar.py create --eth 0.1 --usdc 300

# List all positions
python apestar.py positions

# Collect fees from active position
python apestar.py collect

# Rebalance position
python apestar.py rebalance

# Close a position
python apestar.py close --token-id 12345

# Run the bot continuously
python apestar.py run
```

### Cast Scripts

Quick queries using Foundry's `cast`:

```bash
# Check pool state
./scripts/check_pool.sh

# Get current ETH price
./scripts/get_price.sh

# Check wallet balances
./scripts/check_balance.sh 0xYourWalletAddress

# Calculate tick range
./scripts/calculate_ticks.sh 300  # 300 tick spacings
```

## 🧠 How It Works

### Concentrated Liquidity Strategy

1. **Position Creation**: The bot creates a liquidity position centered around the current price with a configurable tick range (default: ±300 tick spacings).

2. **Range Monitoring**: Continuously monitors if the current price is within the position's range.

3. **Auto-Rebalancing**: When the price moves significantly (controlled by `REBALANCE_THRESHOLD_PERCENT`), the bot:
   - Closes the existing position
   - Collects all tokens and fees
   - Opens a new position centered on the new price

4. **Fee Collection**: Accumulated trading fees can be collected manually or during rebalancing.

### Tick Math

- **Tick Spacing**: The pool uses a specific tick spacing (e.g., 10 for 0.05% fee tier)
- **Price Calculation**: `price = 1.0001^tick`
- **Range Width**: With 300 tick spacings at spacing=10, the range covers ~60% price movement

Example for tick range ±300 (at spacing 10 = ±3000 ticks):
- If current price is $3000
- Lower bound: ~$2220 (-30%)
- Upper bound: ~$4050 (+35%)

## 📁 Architecture

```
apestar-uniswap-auto/
├── src/
│   ├── __init__.py       # Apestar package info
│   ├── config.py         # Configuration management
│   ├── utils.py          # Uniswap V3 math utilities
│   ├── pool.py           # Pool interaction
│   ├── position_manager.py  # NFT position management
│   ├── bot.py            # Main bot logic
│   └── cli.py            # CLI interface
├── abi/
│   ├── uniswap_v3_pool.json
│   ├── erc20.json
│   └── nonfungible_position_manager.json
├── scripts/
│   ├── check_pool.sh
│   ├── get_price.sh
│   ├── check_balance.sh
│   └── calculate_ticks.sh
├── apestar.py            # Entry point
├── requirements.txt
├── env.example
└── README.md
```

## ⚠️ Risk Disclaimer

**USE AT YOUR OWN RISK**

- This is experimental software
- Providing liquidity carries risks including impermanent loss
- Always test with small amounts first
- Never share your private key
- This is not financial advice

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- [Uniswap V3 Docs](https://docs.uniswap.org/)
- [Arbitrum](https://arbitrum.io/)
- [Pool on Arbiscan](https://arbiscan.io/address/0xc6962004f452be9203591991d15f6b388e09e8d0)
- [Foundry Book](https://book.getfoundry.sh/)

---

<p align="center">
  <b>🦍 Powered by Apestar 🦍</b>
</p>
