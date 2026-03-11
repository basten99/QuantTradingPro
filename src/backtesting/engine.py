"""
Backtesting Engine
回测引擎 - 事件驱动的回测框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from enum import Enum
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    MARKET = "market"          # 市场数据事件
    SIGNAL = "signal"          # 交易信号事件
    ORDER = "order"            # 订单事件
    FILL = "fill"              # 成交事件
    PORTFOLIO = "portfolio"    # 组合更新事件


@dataclass
class Event:
    """事件基类"""
    timestamp: pd.Timestamp
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketEvent(Event):
    """市场数据事件"""
    def __post_init__(self):
        self.event_type = EventType.MARKET


@dataclass
class SignalEvent(Event):
    """交易信号事件"""
    symbol: str = ""
    signal: int = 0  # 1: 买入, -1: 卖出, 0: 平仓
    strength: float = 1.0  # 信号强度
    
    def __post_init__(self):
        self.event_type = EventType.SIGNAL


@dataclass
class OrderEvent(Event):
    """订单事件"""
    symbol: str = ""
    order_type: str = "MARKET"  # MARKET, LIMIT, STOP
    quantity: float = 0.0
    direction: str = "BUY"  # BUY, SELL
    price: Optional[float] = None
    
    def __post_init__(self):
        self.event_type = EventType.ORDER


@dataclass
class FillEvent(Event):
    """成交事件"""
    symbol: str = ""
    quantity: float = 0.0
    price: float = 0.0
    commission: float = 0.0
    direction: str = "BUY"
    
    def __post_init__(self):
        self.event_type = EventType.FILL


@dataclass
class PortfolioEvent(Event):
    """组合更新事件"""
    portfolio_value: float = 0.0
    cash: float = 0.0
    positions: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = EventType.PORTFOLIO


class Portfolio:
    """投资组合"""
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        初始化投资组合
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}  # 符号 -> 持仓数量
        self.position_values: Dict[str, float] = {}  # 符号 -> 持仓价值
        self.commission_rate = 0.001  # 佣金率（0.1%）
        
        # 历史记录
        self.history: List[PortfolioEvent] = []
        
    def update(self, timestamp: pd.Timestamp, prices: Dict[str, float]):
        """
        更新组合价值
        
        Args:
            timestamp: 时间戳
            prices: 符号到价格的映射
        """
        total_value = self.cash
        
        for symbol, quantity in self.positions.items():
            if symbol in prices and quantity != 0:
                position_value = quantity * prices[symbol]
                self.position_values[symbol] = position_value
                total_value += position_value
            else:
                self.position_values[symbol] = 0.0
        
        # 记录组合状态
        event = PortfolioEvent(
            timestamp=timestamp,
            portfolio_value=total_value,
            cash=self.cash,
            positions=self.positions.copy()
        )
        self.history.append(event)
        
        return total_value
    
    def execute_order(self, order: OrderEvent, price: float) -> FillEvent:
        """
        执行订单
        
        Args:
            order: 订单事件
            price: 成交价格
            
        Returns:
            成交事件
        """
        # 计算佣金
        trade_value = order.quantity * price
        commission = trade_value * self.commission_rate
        
        if order.direction == "BUY":
            # 买入
            cost = trade_value + commission
            if cost > self.cash:
                raise ValueError(f"Insufficient cash: {self.cash:.2f} < {cost:.2f}")
            
            self.cash -= cost
            if order.symbol in self.positions:
                self.positions[order.symbol] += order.quantity
            else:
                self.positions[order.symbol] = order.quantity
                
        else:  # SELL
            # 卖出
            if order.symbol not in self.positions:
                raise ValueError(f"No position for {order.symbol}")
            
            if abs(self.positions[order.symbol]) < abs(order.quantity):
                raise ValueError(f"Insufficient position: {self.positions[order.symbol]} < {order.quantity}")
            
            proceeds = trade_value - commission
            self.cash += proceeds
            self.positions[order.symbol] -= order.quantity
            
            # 如果持仓为0，移除该符号
            if abs(self.positions[order.symbol]) < 1e-10:
                del self.positions[order.symbol]
                if order.symbol in self.position_values:
                    del self.position_values[order.symbol]
        
        # 创建成交事件
        fill = FillEvent(
            timestamp=order.timestamp,
            symbol=order.symbol,
            quantity=order.quantity,
            price=price,
            commission=commission,
            direction=order.direction
        )
        
        return fill
    
    def get_position(self, symbol: str) -> float:
        """获取持仓数量"""
        return self.positions.get(symbol, 0.0)
    
    def get_position_value(self, symbol: str, price: float) -> float:
        """获取持仓价值"""
        quantity = self.get_position(symbol)
        return quantity * price if quantity != 0 else 0.0
    
    def get_portfolio_history(self) -> pd.DataFrame:
        """获取组合历史数据"""
        if not self.history:
            return pd.DataFrame()
        
        data = []
        for event in self.history:
            row = {
                'timestamp': event.timestamp,
                'portfolio_value': event.portfolio_value,
                'cash': event.cash,
                'positions': str(event.positions)
            }
            data.append(row)
        
        return pd.DataFrame(data).set_index('timestamp')


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        strategy: Any,
        data: pd.DataFrame,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001,
        position_sizing: Callable = None,
    ):
        """
        初始化回测引擎
        
        Args:
            strategy: 交易策略实例
            data: 回测数据（必须包含'close'列）
            initial_capital: 初始资金
            commission_rate: 佣金率
            slippage: 滑点率
            position_sizing: 头寸规模函数
        """
        self.strategy = strategy
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # 设置默认头寸规模函数
        if position_sizing is None:
            self.position_sizing = self.default_position_sizing
        else:
            self.position_sizing = position_sizing
        
        # 初始化组件
        self.portfolio = Portfolio(initial_capital)
        self.events: List[Event] = []
        
        # 回测结果
        self.signals: List[SignalEvent] = []
        self.orders: List[OrderEvent] = []
        self.fills: List[FillEvent] = []
        self.performance: Dict[str, Any] = {}
        
        # 当前状态
        self.current_idx = 0
        self.current_date = None
        self.current_prices = {}
        
    def default_position_sizing(self, portfolio_value: float, price: float) -> float:
        """
        默认头寸规模函数
        
        Args:
            portfolio_value: 组合价值
            price: 当前价格
            
        Returns:
            头寸数量
        """
        # 使用组合价值的10%作为头寸规模
        position_value = portfolio_value * 0.1
        return position_value / price if price > 0 else 0
    
    def run(self) -> Dict[str, Any]:
        """
        运行回测
        
        Returns:
            回测结果
        """
        logger.info("Starting backtest...")
        
        # 确保数据按日期排序
        self.data = self.data.sort_index()
        
        # 主回测循环
        for idx, (date, row) in enumerate(self.data.iterrows()):
            self.current_idx = idx
            self.current_date = date
            
            # 获取当前价格
            self.current_prices = {'close': row['close']}
            if 'open' in row:
                self.current_prices['open'] = row['open']
            if 'high' in row:
                self.current_prices['high'] = row['high']
            if 'low' in row:
                self.current_prices['low'] = row['low']
            
            # 生成市场事件
            market_event = MarketEvent(
                timestamp=date,
                data={'prices': self.current_prices, 'row': row.to_dict()}
            )
            self.events.append(market_event)
            
            # 策略生成信号
            signals = self.strategy.generate_signals(self.data.iloc[:idx+1])
            if not signals.empty and idx < len(signals):
                signal_row = signals.iloc[idx]
                if 'signal' in signal_row and signal_row['signal'] != 0:
                    signal_event = SignalEvent(
                        timestamp=date,
                        symbol='close',  # 默认使用close价格
                        signal=int(signal_row['signal']),
                        strength=abs(signal_row['signal'])
                    )
                    self.events.append(signal_event)
                    self.signals.append(signal_event)
                    
                    # 根据信号生成订单
                    self.generate_order(signal_event)
            
            # 执行订单
            self.execute_orders()
            
            # 更新组合
            self.portfolio.update(date, {'close': row['close']})
        
        # 计算绩效指标
        self.calculate_performance()
        
        logger.info("Backtest completed successfully")
        return self.performance
    
    def generate_order(self, signal: SignalEvent):
        """
        根据信号生成订单
        
        Args:
            signal: 信号事件
        """
        current_price = self.current_prices.get('close', 0)
        if current_price <= 0:
            return
        
        # 获取当前组合价值
        portfolio_value = self.portfolio.update(self.current_date, self.current_prices)
        
        # 计算头寸规模
        quantity = self.position_sizing(portfolio_value, current_price)
        
        if quantity <= 0:
            return
        
        # 确定交易方向
        if signal.signal > 0:
            direction = "BUY"
        elif signal.signal < 0:
            direction = "SELL"
        else:
            # 信号为0表示平仓
            current_position = self.portfolio.get_position(signal.symbol)
            if current_position > 0:
                direction = "SELL"
                quantity = current_position
            elif current_position < 0:
                direction = "BUY"
                quantity = abs(current_position)
            else:
                return  # 无持仓，无需平仓
        
        # 创建订单
        order = OrderEvent(
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            order_type="MARKET",
            quantity=quantity,
            direction=direction,
            price=current_price
        )
        
        self.events.append(order)
        self.orders.append(order)
    
    def execute_orders(self):
        """执行所有待处理订单"""
        orders_to_execute = [e for e in self.events if isinstance(e, OrderEvent)]
        
        for order in orders_to_execute:
            try:
                # 应用滑点
                execution_price = order.price
                if order.direction == "BUY":
                    execution_price *= (1 + self.slippage)
                else:  # SELL
                    execution_price *= (1 - self.slippage)
                
                # 执行订单
                fill = self.portfolio.execute_order(order, execution_price)
                
                # 记录成交
                self.events.append(fill)
                self.fills.append(fill)
                
                # 从待处理事件中移除已执行的订单
                self.events.remove(order)
                
            except Exception as e:
                logger.warning(f"Failed to execute order: {e}")
                self.events.remove(order)
    
    def calculate_performance(self) -> Dict[str, Any]:
        """计算绩效指标"""
        # 获取组合历史
        portfolio_history = self.portfolio.get_portfolio_history()
        if portfolio_history.empty:
            return {}
        
        # 计算收益率
        portfolio_values = portfolio_history['portfolio_value']
        returns = portfolio_values.pct_change().fillna(0)
        
        # 基本指标
        total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
        annual_return = self.calculate_annual_return(returns)
        annual_volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤
        cumulative_returns = (1 + returns).cumprod()
        cumulative_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()
        
        # 胜率和盈亏比
        trade_stats = self.calculate_trade_stats()
        
        # 保存绩效指标
        self.performance = {
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'annual_volatility': float(annual_volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'final_portfolio_value': float(portfolio_values.iloc[-1]),
            'initial_capital': float(self.initial_capital),
            'total_trades': len(self.fills),
            'win_rate': trade_stats['win_rate'],
            'profit_factor': trade_stats['profit_factor'],
            'avg_win': trade_stats['avg_win'],
            'avg_loss': trade_stats['avg_loss'],
            'largest_win': trade_stats['largest_win'],
            'largest_loss': trade_stats['largest_loss'],
            'portfolio_history': portfolio_history,
            'signals': self.signals,
            'orders': self.orders,
            'fills': self.fills,
        }
        
        return self.performance
    
    def calculate_annual_return(self, returns: pd.Series) -> float:
        """计算年化收益率"""
        if len(returns) == 0:
            return 0.0
        
        total_return = (1 + returns).prod() - 1
        years = len(returns) / 252  # 假设252个交易日
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return
        return annual_return
    
    def calculate_trade_stats(self) -> Dict[str, float]:
        """计算交易统计"""
        if not self.fills:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
            }
        
        # 按交易对分组
        trades = []
        current_trade = {}
        
        for fill in self.fills:
            if fill.symbol not in current_trade:
                current_trade[fill.symbol] = {
                    'entries': [],
                    'exits': [],
                    'direction': fill.direction
                }
            
            if fill.direction == "BUY":
                current_trade[fill.symbol]['entries'].append({
                    'price': fill.price,
                    'quantity': fill.quantity,
                    'commission': fill.commission
                })
            else:  # SELL
                current_trade[fill.symbol]['exits'].append({
                    'price': fill.price,
                    'quantity': fill.quantity,
                    'commission': fill.commission
                })
        
        # 计算每笔交易的盈亏
        trade_pnls = []
        
        for symbol, trade in current_trade.items():
            if trade['entries'] and trade['exits']:
                # 计算平均入场价格
                entry_value = sum(e['price'] * e['quantity'] for e in trade['entries'])
                entry_quantity = sum(e['quantity'] for e in trade['entries'])
                entry_price = entry_value / entry_quantity if entry_quantity > 0 else 0
                
                # 计算平均出场价格
                exit_value = sum(e['price'] * e['quantity'] for e in trade['exits'])
                exit_quantity = sum(e['quantity'] for e in trade['exits'])
                exit_price = exit_value / exit_quantity if exit_quantity > 0 else 0
                
                # 计算总佣金
                total_commission = sum(e['commission'] for e in trade['entries']) + \
                                 sum(e['commission'] for e in trade['exits'])
                
                # 计算盈亏
                if trade['direction'] == "BUY":
                    pnl = (exit_price - entry_price) * exit_quantity - total_commission
                    pnl_pct = (exit_price - entry_price) / entry_price if entry