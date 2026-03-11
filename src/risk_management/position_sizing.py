"""
Position Sizing
头寸规模管理 - 凯利公式、固定分数等
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')


@dataclass
class PositionSizingResult:
    """头寸规模计算结果"""
    position_size: float  # 头寸规模（比例）
    quantity: float  # 数量
    risk_amount: float  # 风险金额
    stop_loss: float  # 止损价格
    take_profit: float  # 止盈价格


class PositionSizing:
    """头寸规模管理"""
    
    def __init__(self, portfolio_value: float, risk_per_trade: float = 0.02):
        """
        初始化头寸规模管理器
        
        Args:
            portfolio_value: 组合价值
            risk_per_trade: 每笔交易风险比例（默认2%）
        """
        self.portfolio_value = portfolio_value
        self.risk_per_trade = risk_per_trade
        
    def fixed_fractional(self, entry_price: float, stop_loss: float) -> PositionSizingResult:
        """
        固定分数法
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            
        Returns:
            头寸规模结果
        """
        # 计算风险金额
        risk_amount = self.portfolio_value * self.risk_per_trade
        
        # 计算每单位风险
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit <= 0:
            raise ValueError("Stop loss must be different from entry price")
        
        # 计算头寸数量
        quantity = risk_amount / risk_per_unit
        
        # 计算头寸规模比例
        position_value = quantity * entry_price
        position_size = position_value / self.portfolio_value
        
        return PositionSizingResult(
            position_size=position_size,
            quantity=quantity,
            risk_amount=risk_amount,
            stop_loss=stop_loss,
            take_profit=entry_price + (entry_price - stop_loss) * 2  # 2:1 风险回报比
        )
    
    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        entry_price: float,
        stop_loss: float
    ) -> PositionSizingResult:
        """
        凯利公式
        
        Args:
            win_rate: 胜率
            avg_win: 平均盈利比例
            avg_loss: 平均亏损比例
            entry_price: 入场价格
            stop_loss: 止损价格
            
        Returns:
            头寸规模结果
        """
        # 凯利公式：f* = (bp - q) / b
        # 其中：b = 平均盈利/平均亏损，p = 胜率，q = 败率
        if avg_loss <= 0:
            raise ValueError("Average loss must be positive")
        
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - p
        
        # 凯利分数
        kelly_fraction = (b * p - q) / b if b > 0 else 0
        
        # 通常使用凯利分数的一半（半凯利）以减少风险
        half_kelly = kelly_fraction * 0.5
        
        # 限制在合理范围内（0-25%）
        position_size = max(0.01, min(0.25, half_kelly))
        
        # 计算风险金额
        risk_amount = self.portfolio_value * position_size
        
        # 计算每单位风险
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit <= 0:
            raise ValueError("Stop loss must be different from entry price")
        
        # 计算头寸数量
        quantity = risk_amount / risk_per_unit
        
        return PositionSizingResult(
            position_size=position_size,
            quantity=quantity,
            risk_amount=risk_amount,
            stop_loss=stop_loss,
            take_profit=entry_price + (entry_price - stop_loss) * (b if b > 0 else 2)
        )
    
    def volatility_adjusted(
        self,
        entry_price: float,
        volatility: float,
        atr: float,
        risk_multiplier: float = 2.0
    ) -> PositionSizingResult:
        """
        波动率调整法
        
        Args:
            entry_price: 入场价格
            volatility: 年化波动率
            atr: 平均真实波幅
            risk_multiplier: 风险乘数
            
        Returns:
            头寸规模结果
        """
        # 使用ATR计算止损
        stop_loss = entry_price - atr * risk_multiplier
        
        # 根据波动率调整风险比例
        # 高波动率 => 降低风险比例
        base_risk = self.risk_per_trade
        if volatility > 0.4:  # 40%年化波动率
            adjusted_risk = base_risk * 0.5
        elif volatility > 0.3:
            adjusted_risk = base_risk * 0.75
        elif volatility > 0.2:
            adjusted_risk = base_risk * 0.9
        else:
            adjusted_risk = base_risk
        
        # 计算风险金额
        risk_amount = self.portfolio_value * adjusted_risk
        
        # 计算每单位风险
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit <= 0:
            raise ValueError("Invalid stop loss calculation")
        
        # 计算头寸数量
        quantity = risk_amount / risk_per_unit
        
        # 计算头寸规模比例
        position_value = quantity * entry_price
        position_size = position_value / self.portfolio_value
        
        return PositionSizingResult(
            position_size=position_size,
            quantity=quantity,
            risk_amount=risk_amount,
            stop_loss=stop_loss,
            take_profit=entry_price + (entry_price - stop_loss) * 2
        )
    
    def martingale(
        self,
        entry_price: float,
        stop_loss: float,
        previous_losses: int,
        base_position_size: float = 0.02
    ) -> PositionSizingResult:
        """
        马丁格尔策略（高风险，慎用）
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            previous_losses: 连续亏损次数
            base_position_size: 基础头寸规模比例
            
        Returns:
            头寸规模结果
        """
        # 马丁格尔：每次亏损后加倍头寸
        multiplier = 2 ** previous_losses
        
        # 计算头寸规模
        position_size = base_position_size * multiplier
        
        # 限制最大头寸规模（不超过50%）
        position_size = min(position_size, 0.5)
        
        # 计算风险金额
        risk_amount = self.portfolio_value * position_size
        
        # 计算每单位风险
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit <= 0:
            raise ValueError("Stop loss must be different from entry price")
        
        # 计算头寸数量
        quantity = risk_amount / risk_per_unit
        
        return PositionSizingResult(
            position_size=position_size,
            quantity=quantity,
            risk_amount=risk_amount,
            stop_loss=stop_loss,
            take_profit=entry_price + (entry_price - stop_loss) * 2
        )
    
    def anti_martingale(
        self,
        entry_price: float,
        stop_loss: float,
        previous_wins: int,
        base_position_size: float = 0.02
    ) -> PositionSizingResult:
        """
        反马丁格尔策略（盈利后加仓）
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            previous_wins: 连续盈利次数
            base_position_size: 基础头寸规模比例
            
        Returns:
            头寸规模结果
        """
        # 反马丁格尔：每次盈利后增加头寸
        multiplier = 1.5 ** previous_wins  # 每次盈利增加50%
        
        # 计算头寸规模
        position_size = base_position_size * multiplier
        
        # 限制最大头寸规模（不超过25%）
        position_size = min(position_size, 0.25)
        
        # 计算风险金额
        risk_amount = self.portfolio_value * position_size
        
        # 计算每单位风险
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit <= 0:
            raise ValueError("Stop loss must be different from entry price")
        
        # 计算头寸数量
        quantity = risk_amount / risk_per_unit
        
        return PositionSizingResult(
            position_size=position_size,
            quantity=quantity,
            risk_amount=risk_amount,
            stop_loss=stop_loss,
            take_profit=entry_price + (entry_price - stop_loss) * 2
        )
    
    def optimal_f(
        self,
        returns: pd.Series,
        entry_price: float,
        stop_loss: float
    ) -> PositionSizingResult:
        """
        最优f值法（基于历史收益率）
        
        Args:
            returns: 历史收益率序列
            entry_price: 入场价格
            stop_loss: 止损价格
            
        Returns:
            头寸规模结果
        """
        if len(returns) < 10:
            raise ValueError("Insufficient historical data")
        
        # 计算最优f值
        # 使用模拟方法寻找最大化几何平均收益率的f值
        f_values = np.linspace(0.01, 0.5, 50)
        best_f = 0.01
        best_gmean = -np.inf
        
        for f in f_values:
            # 计算每个f值下的几何平均收益率
            gmean_returns = []
            for ret in returns:
                if ret > 0:
                    gmean_returns.append(1 + f * ret)
                else:
                    gmean_returns.append(1 - f * abs(ret))
            
            gmean = np.prod(gmean_returns) ** (1 / len(gmean_returns))
            
            if gmean > best_gmean:
                best_gmean = gmean
                best_f = f
        
        # 使用最优f值计算头寸规模
        position_size = best_f
        
        # 计算风险金额
        risk_amount = self.portfolio_value * position_size
        
        # 计算每单位风险
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit <= 0:
            raise ValueError("Stop loss must be different from entry price")
        
        # 计算头寸数量
        quantity = risk_amount / risk_per_unit
        
        return PositionSizingResult(
            position_size=position_size,
            quantity=quantity,
            risk_amount=risk_amount,
            stop_loss=stop_loss,
            take_profit=entry_price + (entry_price - stop_loss) * 2
        )


class PositionSizingManager:
    """头寸规模管理器"""
    
    def __init__(
        self,
        portfolio_value: float,
        method: str = "fixed_fractional",
        **kwargs
    ):
        """
        初始化头寸规模管理器
        
        Args:
            portfolio_value: 组合价值
            method: 头寸规模方法
            **kwargs: 方法特定参数
        """
        self.portfolio_value = portfolio_value
        self.method = method
        self.kwargs = kwargs
        
        # 创建头寸规模计算器
        self.calculator = PositionSizing(portfolio_value)
        
        # 交易历史
        self.trade_history: List[Dict] = []
        
    def calculate_position(
        self,
        entry_price: float,
        stop_loss: float,
        **additional_params
    ) -> PositionSizingResult:
        """
        计算头寸规模
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            **additional_params: 额外参数
            
        Returns:
            头寸规模结果
        """
        params = {**self.kwargs, **additional_params}
        
        if self.method == "fixed_fractional":
            result = self.calculator.fixed_fractional(entry_price, stop_loss)
            
        elif self.method == "kelly_criterion":
            win_rate = params.get('win_rate', 0.5)
            avg_win = params.get('avg_win', 0.1)
            avg_loss = params.get('avg_loss', 0.05)
            result = self.calculator.kelly_criterion(
                win_rate, avg_win, avg_loss, entry_price, stop_loss
            )
            
        elif self.method == "volatility_adjusted":
            volatility = params.get('volatility', 0.2)
            atr = params.get('atr', entry_price * 0.02)
            risk_multiplier = params.get('risk_multiplier', 2.0)
            result = self.calculator.volatility_adjusted(
                entry_price, volatility, atr, risk_multiplier
            )
            
        elif self.method == "martingale":
            previous_losses = params.get('previous_losses', 0)
            base_position_size = params.get('base_position_size', 0.02)
            result = self.calculator.martingale(
                entry_price, stop_loss, previous_losses, base_position_size
            )
            
        elif self.method == "anti_martingale":
            previous_wins = params.get('previous_wins', 0)
            base_position_size = params.get('base_position_size', 0.02)
            result = self.calculator.anti_martingale(
                entry_price, stop_loss, previous_wins, base_position_size
            )
            
        elif self.method == "optimal_f":
            returns = params.get('returns', pd.Series([0.01, -0.005, 0.02]))
            result = self.calculator.optimal_f(returns, entry_price, stop_loss)
            
        else:
            raise ValueError(f"Unknown position sizing method: {self.method}")
        
        # 记录交易
        trade_record = {
            'timestamp': pd.Timestamp.now(),
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'position_size': result.position_size,
            'quantity': result.quantity,
            'risk_amount': result.risk_amount,
            'method': self.method
        }
        self.trade_history.append(trade_record)
        
        return result
    
    def update_portfolio_value(self, new_value: float):
        """更新组合价值"""
        self.portfolio_value = new_value
        self.calculator.portfolio_value = new_value
    
    def get_trade_statistics(self) -> Dict[str, float]:
        """获取交易统计"""
        if not self.trade_history:
            return {}
        
        df = pd.DataFrame(self.trade_history)
        
        stats = {
            'total_trades': len(df),
            'avg_position_size': float(df['position_size'].mean()),
            'max_position_size': float(df['position_size'].max()),
            'min_position_size': float(df['position_size'].min()),
            'total_risk_amount': float(df['risk_amount'].sum()),
            'avg_risk_amount': float(df['risk_amount'].mean()),
        }
        
        return stats


# 使用示例
if __name__ == "__main__":
    # 示例：使用固定分数法
    portfolio_value = 100000.0
    manager = PositionSizingManager(
        portfolio_value=portfolio_value,
        method="fixed_fractional",
        risk_per_trade=0.02
    )
    
    entry_price = 100.0
    stop_loss = 95.0
    
    result = manager.calculate_position(entry_price, stop_loss)
    
    print("Position Sizing Results:")
    print(f"  Position Size: {result.position_size:.2%}")
    print(f"  Quantity: {result.quantity:.2f}")
    print(f"  Risk Amount: ${result.risk_amount:.2f}")
    print(f"  Stop Loss: ${result.stop_loss:.2f}")
    print(f"  Take Profit: ${result.take_profit:.2f}")
    
    # 示例：使用凯利公式
    manager2 = PositionSizingManager(
        portfolio_value=portfolio_value,
        method="kelly_criterion",
        win_rate=0.6,
        avg_win=0.15,
        avg_loss=0.08
    )
    
    result2 = manager2.calculate_position(entry_price, stop_loss)
    
    print("\nKelly Criterion Results:")
    print(f"  Position Size: {result2.position_size:.2%}")
    print(f"  Quantity: {result2.quantity:.2f}")