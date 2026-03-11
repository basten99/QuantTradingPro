# QuantTradingPro

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/github/actions/workflow/status/basten99/QuantTradingPro/ci.yml)
![GitHub stars](https://img.shields.io/github/stars/basten99/QuantTradingPro)

**Professional Quantitative Trading Library** - An open-source algorithmic trading framework with automated strategies, backtesting, and risk management.

## 🚀 Features

### 📈 Trading Strategies
- **Mean Reversion**: Statistical arbitrage and pairs trading
- **Trend Following**: Moving average crossover strategies
- **Momentum**: RSI, MACD, and other momentum indicators
- **Arbitrage**: Statistical arbitrage framework
- **Machine Learning**: Classification and regression-based strategies

### 🔧 Data Processing
- **Data Fetching**: Yahoo Finance, Alpha Vantage, and custom APIs
- **Data Cleaning**: Missing value handling, outlier detection
- **Technical Indicators**: 50+ built-in indicators
- **Feature Engineering**: ML-ready feature preparation

### 📊 Backtesting Engine
- **Event-driven architecture**
- **Performance metrics**: Sharpe ratio, max drawdown, CAGR, etc.
- **Visualization**: Equity curves, drawdown charts, heatmaps
- **Multi-timeframe support**

### 🛡️ Risk Management
- **Position Sizing**: Kelly criterion, fixed fractional
- **Stop Loss**: Trailing, volatility-based, time-based
- **Risk Metrics**: VaR, CVaR, stress testing
- **Portfolio Optimization**

## 🏁 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/basten99/QuantTradingPro.git
cd QuantTradingPro

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Basic Usage

```python
from src.strategies.mean_reversion import MeanReversionStrategy
from src.backtesting.engine import BacktestEngine
from src.data.fetchers import YahooFinanceFetcher

# Fetch data
fetcher = YahooFinanceFetcher()
data = fetcher.fetch("AAPL", start="2020-01-01", end="2023-12-31")

# Create strategy
strategy = MeanReversionStrategy(
    lookback_period=20,
    entry_zscore=2.0,
    exit_zscore=0.5
)

# Run backtest
engine = BacktestEngine(strategy, data)
results = engine.run()

# Analyze results
print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
```

## 📚 Examples

Check out our comprehensive examples:

- **Beginner**: Simple moving average strategy, basic backtest
- **Intermediate**: Multi-factor strategy, portfolio optimization
- **Advanced**: Machine learning trading, live trading bot

## 📖 Documentation

Full documentation is available at: [https://basten99.github.io/QuantTradingPro/](https://basten99.github.io/QuantTradingPro/)

- **Tutorials**: Getting started, strategy development, deployment
- **API Reference**: Complete API documentation
- **FAQ**: Common questions and troubleshooting

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 💖 Sponsorship

Support this project and get exclusive benefits:

- **Bronze (¥10/month)**: Early access to new features, exclusive badge
- **Silver (¥50/month)**: Exclusive strategies, priority support
- **Gold (¥200/month)**: Personalized consulting, enterprise features

[Sponsor on GitHub](https://github.com/sponsors/basten99)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/basten99/QuantTradingPro/issues)
- **Email**: basten99@github.com

## 🙏 Acknowledgments

- Thanks to all contributors who have helped shape this project
- Built with ❤️ by the quant trading community

---

**Disclaimer**: This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for every investor. Past performance is not indicative of future results.