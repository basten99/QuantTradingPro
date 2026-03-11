"""
Mean Reversion Strategy
基于统计套利的均值回归策略
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Position(Enum):
    """仓位状态"""
    FLAT = "flat"
    LONG = "long"
    SHORT = "short"


@dataclass
class TradeSignal:
    """交易信号"""
    timestamp: pd.Timestamp
    position: Position
    price: float
    size: float
    reason: str


class MeanReversionStrategy:
    """
    均值回归策略
    
    基于Z-score的统计套利策略：
    1. 计算价格相对于移动平均的Z-score
    2. 当Z-score超过上阈值时做空
    3. 当Z-score低于下阈值时做多
    4. 当Z-score回归到零附近时平仓
    """
    
    def __init__(
        self,
        lookback_period: int = 20,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        stop_loss: float = 0.05,
        take_profit: float = 0.10,
        max_position_size: float = 0.1,
    ):
        """
        初始化均值回归策略
        
        Args:
            lookback_period: 回看周期（用于计算移动平均和标准差）
            entry_zscore: 入场Z-score阈值
            exit_zscore: 出场Z-score阈值
            stop_loss: 止损比例
            take_profit: 止盈比例
            max_position_size: 最大仓位比例（0-1）
        """
        self.lookback_period = lookback_period
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.max_position_size = max_position_size
        
        # 状态变量
        self.position = Position.FLAT
        self.entry_price = 0.0
        self.position_size = 0.0
        self.signals = []
        
    def calculate_zscore(self, prices: pd.Series) -> pd.Series:
        """
        计算Z-score
        
        Args:
            prices: 价格序列
            
        Returns:
            Z-score序列
        """
        rolling_mean = prices.rolling(window=self.lookback_period).mean()
        rolling_std = prices.rolling(window=self.lookback_period).std()
        zscore = (prices - rolling_mean) / rolling_std
        return zscore
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 包含价格的数据框，必须有'close'列
            
        Returns:
            包含信号的数据框
        """
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")
        
        prices = data['close']
        zscore = self.calculate_zscore(prices)
        
        signals = pd.DataFrame(index=data.index)
        signals['price'] = prices
        signals['zscore'] = zscore
        signals['signal'] = 0
        signals['position'] = Position.FLAT.value
        
        # 生成交易信号
        for i in range(self.lookback_period, len(signals)):
            current_zscore = zscore.iloc[i]
            current_price = prices.iloc[i]
            
            # 检查止损止盈
            if self.position != Position.FLAT:
                pnl_pct = (current_price - self.entry_price) / self.entry_price
                if self.position == Position.SHORT:
                    pnl_pct = -pnl_pct
                
                if pnl_pct <= -self.stop_loss:
                    # 止损
                    signals.iloc[i, signals.columns.get_loc('signal')] = 0
                    signals.iloc[i, signals.columns.get_loc('position')] = Position.FLAT.value
                    self.position = Position.FLAT
                    self.signals.append(TradeSignal(
                        timestamp=signals.index[i],
                        position=Position.FLAT,
                        price=current_price,
                        size=self.position_size,
                        reason=f"Stop loss triggered: {pnl_pct:.2%}"
                    ))
                    continue
                elif pnl_pct >= self.take_profit:
                    # 止盈
                    signals.iloc[i, signals.columns.get_loc('signal')] = 0
                    signals.iloc[i, signals.columns.get_loc('position')] = Position.FLAT.value
                    self.position = Position.FLAT
                    self.signals.append(TradeSignal(
                        timestamp=signals.index[i],
                        position=Position.FLAT,
                        price=current_price,
                        size=self.position_size,
                        reason=f"Take profit triggered: {pnl_pct:.2%}"
                    ))
                    continue
            
            # 生成新信号
            if self.position == Position.FLAT:
                if current_zscore > self.entry_zscore:
                    # 做空信号（价格过高）
                    signals.iloc[i, signals.columns.get_loc('signal')] = -1
                    signals.iloc[i, signals.columns.get_loc('position')] = Position.SHORT.value
                    self.position = Position.SHORT
                    self.entry_price = current_price
                    self.position_size = self.max_position_size
                    self.signals.append(TradeSignal(
                        timestamp=signals.index[i],
                        position=Position.SHORT,
                        price=current_price,
                        size=self.position_size,
                        reason=f"Short entry: zscore={current_zscore:.2f}"
                    ))
                elif current_zscore < -self.entry_zscore:
                    # 做多信号（价格过低）
                    signals.iloc[i, signals.columns.get_loc('signal')] = 1
                    signals.iloc[i, signals.columns.get_loc('position')] = Position.LONG.value
                    self.position = Position.LONG
                    self.entry_price = current_price
                    self.position_size = self.max_position_size
                    self.signals.append(TradeSignal(
                        timestamp=signals.index[i],
                        position=Position.LONG,
                        price=current_price,
                        size=self.position_size,
                        reason=f"Long entry: zscore={current_zscore:.2f}"
                    ))
            elif self.position == Position.LONG and abs(current_zscore) < self.exit_zscore:
                # 平多仓
                signals.iloc[i, signals.columns.get_loc('signal')] = 0
                signals.iloc[i, signals.columns.get_loc('position')] = Position.FLAT.value
                self.position = Position.FLAT
                self.signals.append(TradeSignal(
                    timestamp=signals.index[i],
                    position=Position.FLAT,
                    price=current_price,
                    size=self.position_size,
                    reason=f"Long exit: zscore={current_zscore:.2f}"
                ))
            elif self.position == Position.SHORT and abs(current_zscore) < self.exit_zscore:
                # 平空仓
                signals.iloc[i, signals.columns.get_loc('signal')] = 0
                signals.iloc[i, signals.columns.get_loc('position')] = Position.FLAT.value
                self.position = Position.FLAT
                self.signals.append(TradeSignal(
                    timestamp=signals.index[i],
                    position=Position.FLAT,
                    price=current_price,
                    size=self.position_size,
                    reason=f"Short exit: zscore={current_zscore:.2f}"
                ))
            else:
                # 保持现有仓位
                signals.iloc[i, signals.columns.get_loc('position')] = self.position.value
        
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
        winning_trades = len([s for s in self.signals if s.position == Position.FLAT and s.reason.startswith("Take profit")])
        total_trades = len([s for s in self.signals if s.position == Position.FLAT])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'annual_volatility': float(annual_volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
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
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # 价格和信号
        ax1.plot(signals.index, signals['price'], label='Price', color='black', linewidth=1)
        
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
        
        ax1.set_ylabel('Price')
        ax1.set_title('Mean Reversion Strategy - Price and Signals')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Z-score
        ax2.plot(signals.index, signals['zscore'], label='Z-score', color='blue', linewidth=1)
        ax2.axhline(y=self.entry_zscore, color='red', linestyle='--', alpha=0.5, label=f'Entry ({self.entry_zscore})')
        ax2.axhline(y=-self.entry_zscore, color='red', linestyle='--', alpha=0.5)
        ax2.axhline(y=self.exit_zscore, color='green', linestyle='--', alpha=0.5, label=f'Exit ({self.exit_zscore})')
        ax2.axhline(y=-self.exit_zscore, color='green', linestyle='--', alpha=0.5)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        ax2.set_ylabel('Z-score')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 格式化x轴
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        
        plt.show()