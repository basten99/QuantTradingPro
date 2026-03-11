"""
Trend Following Strategy
移动平均线交叉趋势跟踪策略
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    """趋势方向"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class TrendSignal:
    """趋势信号"""
    timestamp: pd.Timestamp
    direction: TrendDirection
    price: float
    fast_ma: float
    slow_ma: float
    reason: str


class TrendFollowingStrategy:
    """
    趋势跟踪策略
    
    基于移动平均线交叉：
    1. 当快线（短期MA）上穿慢线（长期MA）时做多
    2. 当快线下穿慢线时做空
    3. 使用ATR进行动态止损
    4. 使用趋势强度过滤信号
    """
    
    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 30,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        trend_filter_period: int = 50,
        min_trend_strength: float = 0.1,
        position_size: float = 0.1,
    ):
        """
        初始化趋势跟踪策略
        
        Args:
            fast_period: 快线周期
            slow_period: 慢线周期
            atr_period: ATR计算周期
            atr_multiplier: ATR止损乘数
            trend_filter_period: 趋势过滤周期
            min_trend_strength: 最小趋势强度阈值
            position_size: 仓位大小（0-1）
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.trend_filter_period = trend_filter_period
        self.min_trend_strength = min_trend_strength
        self.position_size = position_size
        
        # 状态变量
        self.position = 0  # 1: 多仓, -1: 空仓, 0: 空仓
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.signals = []
        
    def calculate_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """计算移动平均线"""
        return prices.rolling(window=period).mean()
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """计算平均真实波幅（ATR）"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def calculate_trend_strength(self, prices: pd.Series, period: int) -> pd.Series:
        """计算趋势强度（基于线性回归斜率）"""
        from scipy import stats
        
        def get_slope(window):
            if len(window) < 2:
                return 0
            x = np.arange(len(window))
            slope, _, _, _, _ = stats.linregress(x, window)
            return slope
        
        # 使用滚动窗口计算斜率
        slopes = prices.rolling(window=period).apply(get_slope, raw=False)
        # 标准化为0-1范围
        max_slope = slopes.abs().rolling(window=period).max()
        trend_strength = slopes.abs() / max_slope.where(max_slope > 0, 1)
        return trend_strength.fillna(0)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 包含OHLC数据的数据框，必须有'open', 'high', 'low', 'close'列
            
        Returns:
            包含信号的数据框
        """
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Data must contain '{col}' column")
        
        # 计算技术指标
        close = data['close']
        fast_ma = self.calculate_ma(close, self.fast_period)
        slow_ma = self.calculate_ma(close, self.slow_period)
        atr = self.calculate_atr(data['high'], data['low'], close, self.atr_period)
        trend_strength = self.calculate_trend_strength(close, self.trend_filter_period)
        
        # 创建信号数据框
        signals = pd.DataFrame(index=data.index)
        signals['price'] = close
        signals['fast_ma'] = fast_ma
        signals['slow_ma'] = slow_ma
        signals['atr'] = atr
        signals['trend_strength'] = trend_strength
        signals['signal'] = 0
        signals['position'] = 0
        signals['stop_loss'] = 0.0
        signals['take_profit'] = 0.0
        
        # 生成交易信号
        for i in range(max(self.slow_period, self.atr_period, self.trend_filter_period), len(signals)):
            current_price = close.iloc[i]
            current_fast_ma = fast_ma.iloc[i]
            current_slow_ma = slow_ma.iloc[i]
            current_atr = atr.iloc[i]
            current_trend_strength = trend_strength.iloc[i]
            
            # 检查止损止盈
            if self.position != 0:
                if self.position == 1:  # 多仓
                    if current_price <= self.stop_loss:
                        # 止损
                        signals.iloc[i, signals.columns.get_loc('signal')] = 0
                        signals.iloc[i, signals.columns.get_loc('position')] = 0
                        self.position = 0
                        self.signals.append(TrendSignal(
                            timestamp=signals.index[i],
                            direction=TrendDirection.NEUTRAL,
                            price=current_price,
                            fast_ma=current_fast_ma,
                            slow_ma=current_slow_ma,
                            reason=f"Long stop loss triggered at {current_price:.2f}"
                        ))
                        continue
                    elif current_price >= self.take_profit:
                        # 止盈
                        signals.iloc[i, signals.columns.get_loc('signal')] = 0
                        signals.iloc[i, signals.columns.get_loc('position')] = 0
                        self.position = 0
                        self.signals.append(TrendSignal(
                            timestamp=signals.index[i],
                            direction=TrendDirection.NEUTRAL,
                            price=current_price,
                            fast_ma=current_fast_ma,
                            slow_ma=current_slow_ma,
                            reason=f"Long take profit triggered at {current_price:.2f}"
                        ))
                        continue
                elif self.position == -1:  # 空仓
                    if current_price >= self.stop_loss:
                        # 止损
                        signals.iloc[i, signals.columns.get_loc('signal')] = 0
                        signals.iloc[i, signals.columns.get_loc('position')] = 0
                        self.position = 0
                        self.signals.append(TrendSignal(
                            timestamp=signals.index[i],
                            direction=TrendDirection.NEUTRAL,
                            price=current_price,
                            fast_ma=current_fast_ma,
                            slow_ma=current_slow_ma,
                            reason=f"Short stop loss triggered at {current_price:.2f}"
                        ))
                        continue
                    elif current_price <= self.take_profit:
                        # 止盈
                        signals.iloc[i, signals.columns.get_loc('signal')] = 0
                        signals.iloc[i, signals.columns.get_loc('position')] = 0
                        self.position = 0
                        self.signals.append(TrendSignal(
                            timestamp=signals.index[i],
                            direction=TrendDirection.NEUTRAL,
                            price=current_price,
                            fast_ma=current_fast_ma,
                            slow_ma=current_slow_ma,
                            reason=f"Short take profit triggered at {current_price:.2f}"
                        ))
                        continue
            
            # 检查趋势强度过滤
            if current_trend_strength < self.min_trend_strength:
                # 趋势强度不足，不交易
                signals.iloc[i, signals.columns.get_loc('position')] = self.position
                continue
            
            # 生成新信号
            prev_fast_ma = fast_ma.iloc[i-1]
            prev_slow_ma = slow_ma.iloc[i-1]
            
            # 金叉：快线上穿慢线
            if (prev_fast_ma <= prev_slow_ma) and (current_fast_ma > current_slow_ma):
                if self.position != 1:  # 如果不是已经在多仓
                    signals.iloc[i, signals.columns.get_loc('signal')] = 1
                    signals.iloc[i, signals.columns.get_loc('position')] = 1
                    self.position = 1
                    self.entry_price = current_price
                    self.stop_loss = current_price - current_atr * self.atr_multiplier
                    self.take_profit = current_price + current_atr * self.atr_multiplier * 2
                    
                    signals.iloc[i, signals.columns.get_loc('stop_loss')] = self.stop_loss
                    signals.iloc[i, signals.columns.get_loc('take_profit')] = self.take_profit
                    
                    self.signals.append(TrendSignal(
                        timestamp=signals.index[i],
                        direction=TrendDirection.BULLISH,
                        price=current_price,
                        fast_ma=current_fast_ma,
                        slow_ma=current_slow_ma,
                        reason=f"Golden cross: fast MA ({current_fast_ma:.2f}) > slow MA ({current_slow_ma:.2f})"
                    ))
            
            # 死叉：快线下穿慢线
            elif (prev_fast_ma >= prev_slow_ma) and (current_fast_ma < current_slow_ma):
                if self.position != -1:  # 如果不是已经在空仓
                    signals.iloc[i, signals.columns.get_loc('signal')] = -1
                    signals.iloc[i, signals.columns.get_loc('position')] = -1
                    self.position = -1
                    self.entry_price = current_price
                    self.stop_loss = current_price + current_atr * self.atr_multiplier
                    self.take_profit = current_price - current_atr * self.atr_multiplier * 2
                    
                    signals.iloc[i, signals.columns.get_loc('stop_loss')] = self.stop_loss
                    signals.iloc[i, signals.columns.get_loc('take_profit')] = self.take_profit
                    
                    self.signals.append(TrendSignal(
                        timestamp=signals.index[i],
                        direction=TrendDirection.BEARISH,
                        price=current_price,
                        fast_ma=current_fast_ma,
                        slow_ma=current_slow_ma,
                        reason=f"Death cross: fast MA ({current_fast_ma:.2f}) < slow MA ({current_slow_ma:.2f})"
                    ))
            else:
                # 保持现有仓位
                signals.iloc[i, signals.columns.get_loc('position')] = self.position
                if self.position != 0:
                    signals.iloc[i, signals.columns.get_loc('stop_loss')] = self.stop_loss
                    signals.iloc[i, signals.columns.get_loc('take_profit')] = self.take_profit
        
        return signals
    
    def get_performance_metrics(self, signals: pd.DataFrame) -> Dict[str, float]:
        """
        计算策略绩效指标
        
        Args:
            signals: 包含信号和价格的数据框
            
        Returns:
            绩效指标字典
        """
        if 'signal' not in signals.columns or 'price' not in signals.columns:
            raise ValueError("Signals must contain 'signal' and 'price' columns")
        
        # 计算收益率
        returns = signals['price'].pct_change().fillna(0)
        strategy_returns = returns * signals['signal'].shift(1).fillna(0)
        
        # 计算累计收益率
        cumulative_returns = (1 + strategy_returns).cumprod()
        
        # 计算绩效指标
        total_return = cumulative_returns.iloc[-1] - 1 if len(cumulative_returns) > 0 else 0
        
        # 年化收益率（假设252个交易日）
        if len(strategy_returns) > 252:
            annual_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1
        else:
            annual_return = total_return
        
        # 年化波动率
        annual_volatility = strategy_returns.std() * np.sqrt(252)
        
        # 夏普比率（假设无风险利率为0）
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤
        cumulative_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()
        
        # 胜率
        winning_trades = len([s for s in self.signals if "take profit" in s.reason.lower()])
        total_trades = len([s for s in self.signals if "triggered" in s.reason.lower()])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 平均盈亏比
        profitable_trades = []
        losing_trades = []
        
        for i in range(1, len(self.signals)):
            if "triggered" in self.signals[i].reason.lower():
                prev_signal = self.signals[i-1]
                entry_price = prev_signal.price
                exit_price = self.signals[i].price
                
                if "Long" in prev_signal.reason:
                    pnl_pct = (exit_price - entry_price) / entry_price
                else:  # Short
                    pnl_pct = (entry_price - exit_price) / entry_price
                
                if pnl_pct > 0:
                    profitable_trades.append(pnl_pct)
                else:
                    losing_trades.append(abs(pnl_pct))
        
        avg_win = np.mean(profitable_trades) if profitable_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'annual_volatility': float(annual_volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'profit_loss_ratio': float(profit_loss_ratio),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
        }
    
    def plot_signals(self, signals: pd.DataFrame, save_path: Optional[str] = None):
        """
        绘制信号图表
        
        Args:
            signals: 包含信号和价格的数据框
            save_path: 保存路径（可选）
        """
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        
        # 价格和移动平均线
        ax1.plot(signals.index, signals['price'], label='Price', color='black', linewidth=1, alpha=0.7)
        ax1.plot(signals.index, signals['fast_ma'], label=f'Fast MA ({self.fast_period})', 
                color='blue', linewidth=1.5, alpha=0.8)
        ax1.plot(signals.index, signals['slow_ma'], label=f'Slow MA ({self.slow_period})', 
                color='red', linewidth=1.5, alpha=0.8)
        
        # 标记买入信号
        buy_signals = signals[signals['signal'] == 1]
        if len(buy_signals) > 0:
            ax1.scatter(buy_signals.index, buy_signals['price'], 
                       color='green', marker='^', s=100, label='Buy', zorder=5)
        
        # 标记卖出信号
        sell_signals = signals[signals['signal'] == -1]
        if len(sell_signals) > 0:
            ax1.scatter(sell_signals.index, sell_signals['price'], 
                       color='red', marker='v', s=100, label='Sell', zorder=5)
        
        # 标记止损止盈线
        for i in range(len(signals)):
            if signals['stop_loss'].iloc[i] != 0:
                ax1.scatter(signals.index[i], signals['stop_loss'].iloc[i], 
                           color='orange', marker='x', s=50, alpha=0.5, zorder=4)
            if signals['take_profit'].iloc[i] != 0:
                ax1.scatter(signals.index[i], signals['take_profit'].iloc[i], 
                           color='purple', marker='x', s=50, alpha=0.5, zorder=4)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig

    def get_default_parameters(self) -> Dict[str, Any]:
        """获取默认参数"""
        return {
            'fast_period': 10,
            'slow_period': 30,
            'position_size': 0.1,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.05,
        }
