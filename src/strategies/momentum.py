"""
Momentum Strategy
动量策略 - 基于RSI、MACD等动量指标
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MomentumSignal(Enum):
    """动量信号"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class TradeAction:
    """交易动作"""
    timestamp: pd.Timestamp
    signal: MomentumSignal
    price: float
    rsi: float
    macd: float
    macd_signal: float
    reason: str


class MomentumStrategy:
    """
    动量策略
    
    基于多个动量指标：
    1. RSI（相对强弱指标）：超买超卖信号
    2. MACD（移动平均收敛发散）：趋势动量信号
    3. 价格突破：N日新高新低
    4. 成交量确认：成交量放大确认信号
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_overbought: float = 70,
        rsi_oversold: float = 30,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        breakout_period: int = 20,
        volume_multiplier: float = 1.5,
        position_size: float = 0.1,
    ):
        """
        初始化动量策略
        
        Args:
            rsi_period: RSI计算周期
            rsi_overbought: RSI超买阈值
            rsi_oversold: RSI超卖阈值
            macd_fast: MACD快线周期
            macd_slow: MACD慢线周期
            macd_signal: MACD信号线周期
            breakout_period: 突破周期
            volume_multiplier: 成交量放大倍数
            position_size: 仓位大小（0-1）
        """
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.breakout_period = breakout_period
        self.volume_multiplier = volume_multiplier
        self.position_size = position_size
        
        # 状态变量
        self.position = 0  # 1: 多仓, -1: 空仓, 0: 空仓
        self.entry_price = 0.0
        self.actions = []
        
    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int, slow: int, signal: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_histogram = macd - macd_signal
        return macd, macd_signal, macd_histogram
    
    def calculate_breakouts(self, prices: pd.Series, period: int) -> Tuple[pd.Series, pd.Series]:
        """计算突破信号"""
        rolling_high = prices.rolling(window=period).max()
        rolling_low = prices.rolling(window=period).min()
        
        new_high = (prices == rolling_high) & (prices.shift(1) < rolling_high.shift(1))
        new_low = (prices == rolling_low) & (prices.shift(1) > rolling_low.shift(1))
        
        return new_high, new_low
    
    def calculate_volume_confirmation(self, volume: pd.Series, period: int = 20) -> pd.Series:
        """计算成交量确认"""
        volume_ma = volume.rolling(window=period).mean()
        volume_ratio = volume / volume_ma
        return volume_ratio
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 包含OHLCV数据的数据框，必须有'open', 'high', 'low', 'close', 'volume'列
            
        Returns:
            包含信号的数据框
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Data must contain '{col}' column")
        
        # 计算技术指标
        close = data['close']
        volume = data['volume']
        
        rsi = self.calculate_rsi(close, self.rsi_period)
        macd, macd_signal, macd_histogram = self.calculate_macd(
            close, self.macd_fast, self.macd_slow, self.macd_signal
        )
        new_high, new_low = self.calculate_breakouts(close, self.breakout_period)
        volume_ratio = self.calculate_volume_confirmation(volume)
        
        # 创建信号数据框
        signals = pd.DataFrame(index=data.index)
        signals['price'] = close
        signals['volume'] = volume
        signals['rsi'] = rsi
        signals['macd'] = macd
        signals['macd_signal'] = macd_signal
        signals['macd_histogram'] = macd_histogram
        signals['new_high'] = new_high
        signals['new_low'] = new_low
        signals['volume_ratio'] = volume_ratio
        signals['signal'] = 0
        signals['position'] = 0
        signals['momentum_score'] = 0.0
        
        # 生成交易信号
        for i in range(max(self.rsi_period, self.macd_slow, self.breakout_period, 20), len(signals)):
            current_price = close.iloc[i]
            current_rsi = rsi.iloc[i]
            current_macd = macd.iloc[i]
            current_macd_signal = macd_signal.iloc[i]
            current_macd_hist = macd_histogram.iloc[i]
            is_new_high = new_high.iloc[i]
            is_new_low = new_low.iloc[i]
            current_volume_ratio = volume_ratio.iloc[i]
            
            # 计算动量分数（0-100）
            momentum_score = 50  # 中性起点
            
            # RSI贡献
            if current_rsi < self.rsi_oversold:
                momentum_score += 20  # 超卖，看涨
            elif current_rsi > self.rsi_overbought:
                momentum_score -= 20  # 超买，看跌
            elif current_rsi < 50:
                momentum_score += 10  # 偏弱，但未超卖
            else:
                momentum_score -= 10  # 偏强，但未超买
            
            # MACD贡献
            if current_macd > current_macd_signal:
                momentum_score += 15  # MACD金叉
            else:
                momentum_score -= 15  # MACD死叉
            
            if current_macd_hist > 0:
                momentum_score += 5  # 柱状图为正
            else:
                momentum_score -= 5  # 柱状图为负
            
            # 突破贡献
            if is_new_high:
                momentum_score += 10  # 创N日新高
            if is_new_low:
                momentum_score -= 10  # 创N日新低
            
            # 成交量确认
            if current_volume_ratio > self.volume_multiplier:
                # 成交量放大，加强当前信号
                if momentum_score > 50:
                    momentum_score += 10
                elif momentum_score < 50:
                    momentum_score -= 10
            
            # 限制分数在0-100之间
            momentum_score = max(0, min(100, momentum_score))
            signals.iloc[i, signals.columns.get_loc('momentum_score')] = momentum_score
            
            # 根据动量分数生成信号
            if momentum_score >= 80:
                signal_value = 2  # 强烈买入
                signal_type = MomentumSignal.STRONG_BUY
                reason = f"Strong buy: momentum_score={momentum_score:.1f}, RSI={current_rsi:.1f}, MACD bullish"
            elif momentum_score >= 60:
                signal_value = 1  # 买入
                signal_type = MomentumSignal.BUY
                reason = f"Buy: momentum_score={momentum_score:.1f}, RSI={current_rsi:.1f}"
            elif momentum_score <= 20:
                signal_value = -2  # 强烈卖出
                signal_type = MomentumSignal.STRONG_SELL
                reason = f"Strong sell: momentum_score={momentum_score:.1f}, RSI={current_rsi:.1f}, MACD bearish"
            elif momentum_score <= 40:
                signal_value = -1  # 卖出
                signal_type = MomentumSignal.SELL
                reason = f"Sell: momentum_score={momentum_score:.1f}, RSI={current_rsi:.1f}"
            else:
                signal_value = 0  # 中性
                signal_type = MomentumSignal.NEUTRAL
                reason = f"Neutral: momentum_score={momentum_score:.1f}"
            
            # 检查是否需要改变仓位
            if signal_value > 0 and self.position <= 0:
                # 买入信号且当前不是多仓
                signals.iloc[i, signals.columns.get_loc('signal')] = signal_value
                signals.iloc[i, signals.columns.get_loc('position')] = 1
                self.position = 1
                self.entry_price = current_price
                
                self.actions.append(TradeAction(
                    timestamp=signals.index[i],
                    signal=signal_type,
                    price=current_price,
                    rsi=current_rsi,
                    macd=current_macd,
                    macd_signal=current_macd_signal,
                    reason=reason
                ))
            elif signal_value < 0 and self.position >= 0:
                # 卖出信号且当前不是空仓
                signals.iloc[i, signals.columns.get_loc('signal')] = signal_value
                signals.iloc[i, signals.columns.get_loc('position')] = -1
                self.position = -1
                self.entry_price = current_price
                
                self.actions.append(TradeAction(
                    timestamp=signals.index[i],
                    signal=signal_type,
                    price=current_price,
                    rsi=current_rsi,
                    macd=current_macd,
                    macd_signal=current_macd_signal,
                    reason=reason
                ))
            elif signal_value == 0 and self.position != 0:
                # 中性信号，平仓
                signals.iloc[i, signals.columns.get_loc('signal')] = 0
                signals.iloc[i, signals.columns.get_loc('position')] = 0
                
                # 计算盈亏
                if self.position == 1:
                    pnl_pct = (current_price - self.entry_price) / self.entry_price
                    pnl_text = f"Long closed: PnL={pnl_pct:.2%}"
                else:
                    pnl_pct = (self.entry_price - current_price) / self.entry_price
                    pnl_text = f"Short closed: PnL={pnl_pct:.2%}"
                
                self.actions.append(TradeAction(
                    timestamp=signals.index[i],
                    signal=MomentumSignal.NEUTRAL,
                    price=current_price,
                    rsi=current_rsi,
                    macd=current_macd,
                    macd_signal=current_macd_signal,
                    reason=f"Position closed - {pnl_text}"
                ))
                
                self.position = 0
                self.entry_price = 0.0
            else:
                # 保持现有仓位
                signals.iloc[i, signals.columns.get_loc('position')] = self.position
        
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
        
        # 将信号转换为仓位（强烈信号权重加倍）
        position = signals['position'].copy()
        strong_signals = abs(signals['signal']) == 2
        position[strong_signals] = position[strong_signals] * 1.5  # 强烈信号仓位增加50%
        
        strategy_returns = returns * position.shift(1).fillna(0)
        
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
        trades = []
        for i in range(1, len(self.actions)):
            if self.actions[i].signal == MomentumSignal.NEUTRAL and i > 0:
                prev_action = self.actions[i-1]
                entry_price = prev_action.price
                exit_price = self.actions[i].price
                
                if prev_action.signal in [MomentumSignal.BUY, MomentumSignal.STRONG_BUY]:
                    pnl_pct = (exit_price - entry_price) / entry_price
                    trades.append((True, pnl_pct, "long"))
                elif prev_action.signal in [MomentumSignal.SELL, MomentumSignal.STRONG_SELL]:
                    pnl_pct = (entry_price - exit_price) / entry_price
                    trades.append((True, pnl_pct, "short"))
        
        winning_trades = len([t for t in trades if t[1] > 0])
        total_trades = len(trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 平均盈亏比
        profitable_trades = [t[1] for t in trades if t[1] > 0]
        losing_trades = [abs(t[1]) for t in trades if t[1] < 0]
        
        avg_win = np.mean(profitable_trades) if profitable_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # 平均持仓时间（以交易日计）
        if trades:
            avg_holding_period = len(signals) / total_trades
        else:
            avg_holding_period = 0
        
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
            'avg_holding_period': float(avg_holding_period),
            'avg_momentum_score': float(signals['momentum_score'].mean()),
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
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        
        # 价格和信号
        ax1.plot(signals.index, signals['price'], label='Price', color='black', linewidth=