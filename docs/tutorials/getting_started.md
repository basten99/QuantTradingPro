# Getting Started with QuantTradingPro

欢迎使用 QuantTradingPro！这是一个专业的开源量化交易库，旨在帮助开发者、交易员和研究人员快速构建、测试和部署量化交易策略。

## 🚀 快速开始

### 安装

#### 从PyPI安装（推荐）

```bash
pip install quanttradingpro
```

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/basten99/QuantTradingPro.git
cd QuantTradingPro

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install -e .
```

### 基本使用

#### 1. 获取数据

```python
from src.data.fetchers import YahooFinanceFetcher, DataFetchConfig

# 创建数据获取器
fetcher = YahooFinanceFetcher()

# 配置数据获取
config = DataFetchConfig(
    symbol="AAPL",
    start_date="2020-01-01",
    end_date="2023-12-31",
    interval="1d"
)

# 获取数据
data = fetcher.fetch(config)
print(f"获取了 {len(data)} 行数据")
```

#### 2. 创建策略

```python
from src.strategies.mean_reversion import MeanReversionStrategy

# 创建均值回归策略
strategy = MeanReversionStrategy(
    lookback_period=20,
    entry_zscore=2.0,
    exit_zscore=0.5,
    stop_loss=0.05,
    take_profit=0.10
)

# 生成交易信号
signals = strategy.generate_signals(data)
```

#### 3. 运行回测

```python
from src.backtesting.engine import BacktestEngine

# 创建回测引擎
engine = BacktestEngine(
    strategy=strategy,
    data=data,
    initial_capital=100000.0,
    commission_rate=0.001,
    slippage=0.001
)

# 运行回测
performance = engine.run()

# 查看结果
print(f"总收益率: {performance['total_return']:.2%}")
print(f"夏普比率: {performance['sharpe_ratio']:.2f}")
print(f"最大回撤: {performance['max_drawdown']:.2%}")
```

## 📚 核心概念

### 1. 数据获取 (Data Fetchers)

QuantTradingPro 支持多种数据源：

- **Yahoo Finance**: 免费、实时的股票数据
- **Alpha Vantage**: 专业的金融数据API
- **CSV文件**: 导入自定义数据
- **数据库**: 支持SQL数据库连接

### 2. 交易策略 (Strategies)

内置多种交易策略：

- **均值回归 (Mean Reversion)**: 基于统计套利
- **趋势跟踪 (Trend Following)**: 移动平均线交叉
- **动量策略 (Momentum)**: RSI、MACD等指标
- **套利策略 (Arbitrage)**: 统计套利框架
- **机器学习策略 (Machine Learning)**: 基于分类和回归

### 3. 回测引擎 (Backtesting Engine)

事件驱动的回测框架：

- **真实模拟**: 考虑佣金、滑点、流动性
- **多时间框架**: 支持日线、小时线、分钟线
- **绩效分析**: 完整的风险收益指标
- **可视化**: 自动生成图表和报告

### 4. 风险管理 (Risk Management)

专业的风险管理工具：

- **头寸规模管理**: 凯利公式、固定分数等
- **止损止盈**: 动态止损、移动止损
- **风险价值 (VaR)**: 计算投资组合风险
- **压力测试**: 模拟极端市场情况

## 🔧 项目结构

```
QuantTradingPro/
├── src/                    # 源代码
│   ├── strategies/        # 交易策略
│   ├── data/             # 数据处理
│   ├── backtesting/      # 回测引擎
│   ├── risk_management/  # 风险管理
│   └── utils/            # 工具函数
├── examples/             # 示例代码
│   ├── beginner/        # 初学者示例
│   ├── intermediate/    # 进阶示例
│   └── advanced/        # 高级示例
├── docs/                # 文档
├── tests/              # 测试代码
└── .github/            # GitHub配置
```

## 🎯 示例项目

### 初学者示例

1. **简单移动平均策略**: `examples/beginner/simple_ma_strategy.py`
2. **基础回测框架**: `examples/beginner/basic_backtest.ipynb`

### 进阶示例

1. **多因子策略**: `examples/intermediate/multi_factor_strategy.py`
2. **组合优化**: `examples/intermediate/portfolio_optimization.ipynb`

### 高级示例

1. **机器学习交易策略**: `examples/advanced/ml_trading_strategy.py`
2. **实盘交易机器人**: `examples/advanced/live_trading_bot.py`

## 📊 绩效指标

QuantTradingPro 提供完整的绩效分析：

### 收益指标
- **总收益率 (Total Return)**: 投资期间的总收益
- **年化收益率 (Annual Return)**: 折算为年化的收益
- **累计收益率 (Cumulative Return)**: 随时间累积的收益

### 风险指标
- **年化波动率 (Annual Volatility)**: 收益的波动程度
- **最大回撤 (Max Drawdown)**: 最大亏损幅度
- **夏普比率 (Sharpe Ratio)**: 风险调整后收益
- **索提诺比率 (Sortino Ratio)**: 下行风险调整后收益

### 交易统计
- **胜率 (Win Rate)**: 盈利交易的比例
- **盈亏比 (Profit Factor)**: 总盈利/总亏损
- **平均持仓时间**: 交易的平均持有期
- **交易频率**: 单位时间的交易次数

## 🛠️ 开发指南

### 创建自定义策略

```python
from src.strategies.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, param1, param2):
        super().__init__()
        self.param1 = param1
        self.param2 = param2
    
    def generate_signals(self, data):
        # 实现你的交易逻辑
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        
        # 你的策略代码...
        
        return signals
```

### 添加新数据源

```python
from src.data.fetchers import DataFetcher

class MyDataFetcher(DataFetcher):
    def fetch(self, config):
        # 实现数据获取逻辑
        pass
    
    def validate_data(self, data):
        # 实现数据验证逻辑
        pass
```

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 报告问题
- 使用 [GitHub Issues](https://github.com/basten99/QuantTradingPro/issues) 报告bug或请求功能
- 提供详细的复现步骤和环境信息

### 提交代码
1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范
- 遵循 PEP 8 编码规范
- 使用类型提示 (Type Hints)
- 编写单元测试
- 更新相关文档

## 📞 支持与帮助

### 文档
- [完整API文档](https://basten99.github.io/QuantTradingPro/)
- [示例代码](https://github.com/basten99/QuantTradingPro/tree/main/examples)
- [常见问题](https://github.com/basten99/QuantTradingPro/wiki/FAQ)

### 社区
- [GitHub Discussions](https://github.com/basten99/QuantTradingPro/discussions)
- [Discord频道](https://discord.gg/your-invite-link)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/quanttradingpro)

### 商业支持
- **企业版**: 定制功能和企业支持
- **咨询服务**: 策略开发和部署
- **培训服务**: 量化交易培训课程

## 📄 许可证

QuantTradingPro 使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者、测试者和用户！

特别感谢：
- 开源社区的宝贵反馈
- 贡献者的代码提交
- 赞助者的慷慨支持

---

**开始你的量化交易之旅吧！** 🚀

如果有任何问题或建议，请随时联系我们或在GitHub上创建Issue。