"""
Simple Moving Average Strategy Example
简单移动平均线策略示例
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.data.fetchers import YahooFinanceFetcher, DataFetchConfig
from src.strategies.trend_following import TrendFollowingStrategy
from src.backtesting.engine import BacktestEngine


def main():
    """主函数"""
    print("=" * 60)
    print("QuantTradingPro - Simple MA Strategy Example")
    print("=" * 60)
    
    # 1. 获取数据
    print("\n1. 获取数据...")
    fetcher = YahooFinanceFetcher()
    
    config = DataFetchConfig(
        symbol="AAPL",
        start_date="2020-01-01",
        end_date="2023-12-31",
        interval="1d"
    )
    
    try:
        data = fetcher.fetch(config)
        print(f"✓ 成功获取 {len(data)} 行数据")
        print(f"  日期范围: {data.index.min()} 到 {data.index.max()}")
        print(f"  列: {', '.join(data.columns.tolist())}")
    except Exception as e:
        print(f"✗ 数据获取失败: {e}")
        return
    
    # 2. 创建策略
    print("\n2. 创建策略...")
    strategy = TrendFollowingStrategy(
        fast_period=10,
        slow_period=30,
        atr_period=14,
        atr_multiplier=2.0,
        trend_filter_period=50,
        min_trend_strength=0.1,
        position_size=0.1
    )
    print("✓ 趋势跟踪策略已创建")
    print(f"  快线周期: {strategy.fast_period}")
    print(f"  慢线周期: {strategy.slow_period}")
    print(f"  ATR周期: {strategy.atr_period}")
    
    # 3. 生成信号
    print("\n3. 生成交易信号...")
    signals = strategy.generate_signals(data)
    print(f"✓ 生成 {len(signals)} 个信号点")
    
    # 统计信号
    buy_signals = signals[signals['signal'] == 1]
    sell_signals = signals[signals['signal'] == -1]
    print(f"  买入信号: {len(buy_signals)} 个")
    print(f"  卖出信号: {len(sell_signals)} 个")
    
    # 4. 运行回测
    print("\n4. 运行回测...")
    engine = BacktestEngine(
        strategy=strategy,
        data=data,
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    performance = engine.run()
    print("✓ 回测完成")
    
    # 5. 显示结果
    print("\n5. 绩效结果:")
    print("-" * 40)
    print(f"初始资金: ${performance['initial_capital']:,.2f}")
    print(f"最终资金: ${performance['final_portfolio_value']:,.2f}")
    print(f"总收益率: {performance['total_return']:.2%}")
    print(f"年化收益率: {performance['annual_return']:.2%}")
    print(f"年化波动率: {performance['annual_volatility']:.2%}")
    print(f"夏普比率: {performance['sharpe_ratio']:.2f}")
    print(f"最大回撤: {performance['max_drawdown']:.2%}")
    print(f"总交易次数: {performance['total_trades']}")
    print(f"胜率: {performance['win_rate']:.2%}")
    print(f"盈亏比: {performance['profit_factor']:.2f}")
    
    # 6. 绘制图表
    print("\n6. 生成图表...")
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # 价格和移动平均线
    ax1.plot(data.index, data['close'], label='Price', color='black', linewidth=1, alpha=0.7)
    ax1.plot(signals.index, signals['fast_ma'], label='Fast MA (10)', color='blue', linewidth=1.5, alpha=0.8)
    ax1.plot(signals.index, signals['slow_ma'], label='Slow MA (30)', color='red', linewidth=1.5, alpha=0.8)
    
    # 标记买入信号
    if len(buy_signals) > 0:
        ax1.scatter(buy_signals.index, buy_signals['price'], 
                   color='green', marker='^', s=100, label='Buy', zorder=5)
    
    # 标记卖出信号
    if len(sell_signals) > 0:
        ax1.scatter(sell_signals.index, sell_signals['price'], 
                   color='red', marker='v', s=100, label='Sell', zorder=5)
    
    ax1.set_title('AAPL - Price and Moving Averages')
    ax1.set_ylabel('Price ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 组合价值曲线
    portfolio_history = performance['portfolio_history']
    ax2.plot(portfolio_history.index, portfolio_history['portfolio_value'], 
            label='Portfolio Value', color='green', linewidth=2)
    ax2.axhline(y=performance['initial_capital'], color='red', linestyle='--', 
               alpha=0.5, label='Initial Capital')
    ax2.set_title('Portfolio Value Over Time')
    ax2.set_ylabel('Value ($)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 收益率分布
    returns = portfolio_history['portfolio_value'].pct_change().dropna()
    ax3.hist(returns, bins=50, alpha=0.7, color='blue', edgecolor='black')
    ax3.axvline(x=returns.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {returns.mean():.4f}')
    ax3.axvline(x=returns.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {returns.median():.4f}')
    ax3.set_title('Daily Returns Distribution')
    ax3.set_xlabel('Daily Return')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 回撤曲线
    cumulative_returns = (1 + returns).cumprod()
    cumulative_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - cumulative_max) / cumulative_max
    
    ax4.fill_between(drawdown.index, drawdown * 100, 0, 
                     where=drawdown < 0, color='red', alpha=0.3)
    ax4.plot(drawdown.index, drawdown * 100, color='red', linewidth=1)
    ax4.axhline(y=performance['max_drawdown'] * 100, color='darkred', 
               linestyle='--', alpha=0.5, label=f'Max Drawdown: {performance["max_drawdown"]:.2%}')
    ax4.set_title('Portfolio Drawdown')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Drawdown (%)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('simple_ma_strategy_results.png', dpi=300, bbox_inches='tight')
    print("✓ 图表已保存为 'simple_ma_strategy_results.png'")
    
    # 7. 保存结果到CSV
    print("\n7. 保存详细结果...")
    
    # 保存信号
    signals_to_save = signals[['price', 'fast_ma', 'slow_ma', 'signal', 'position']].copy()
    signals_to_save.to_csv('trading_signals.csv')
    print("✓ 交易信号已保存为 'trading_signals.csv'")
    
    # 保存组合历史
    portfolio_history.to_csv('portfolio_history.csv')
    print("✓ 组合历史已保存为 'portfolio_history.csv'")
    
    # 保存绩效摘要
    summary = {
        'Metric': [
            'Initial Capital', 'Final Portfolio Value', 'Total Return',
            'Annual Return', 'Annual Volatility', 'Sharpe Ratio',
            'Max Drawdown', 'Total Trades', 'Win Rate', 'Profit Factor'
        ],
        'Value': [
            f"${performance['initial_capital']:,.2f}",
            f"${performance['final_portfolio_value']:,.2f}",
            f"{performance['total_return']:.2%}",
            f"{performance['annual_return']:.2%}",
            f"{performance['annual_volatility']:.2%}",
            f"{performance['sharpe_ratio']:.2f}",
            f"{performance['max_drawdown']:.2%}",
            f"{performance['total_trades']}",
            f"{performance['win_rate']:.2%}",
            f"{performance['profit_factor']:.2f}"
        ]
    }
    
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv('performance_summary.csv', index=False)
    print("✓ 绩效摘要已保存为 'performance_summary.csv'")
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("生成的文件:")
    print("  - simple_ma_strategy_results.png (图表)")
    print("  - trading_signals.csv (交易信号)")
    print("  - portfolio_history.csv (组合历史)")
    print("  - performance_summary.csv (绩效摘要)")
    print("=" * 60)


if __name__ == "__main__":
    main()