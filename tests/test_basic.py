"""
Basic tests for QuantTradingPro
"""

import pytest
import numpy as np
import pandas as pd


def test_import():
    """Test that core modules can be imported"""
    try:
        from src.strategies.mean_reversion import MeanReversionStrategy
        from src.data.fetchers import DataFetcher
        from src.risk_management.position_sizing import PositionSizer
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_data_structures():
    """Test basic data structures"""
    # Test numpy
    arr = np.array([1, 2, 3])
    assert arr.shape == (3,)
    
    # Test pandas
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    assert df.shape == (3, 2)
    
    # Test datetime
    dates = pd.date_range('2024-01-01', periods=5)
    assert len(dates) == 5


def test_mean_reversion_strategy():
    """Test mean reversion strategy initialization"""
    from src.strategies.mean_reversion import MeanReversionStrategy, Position
    
    strategy = MeanReversionStrategy(
        lookback_period=20,
        zscore_threshold=2.0,
        position_size=0.1
    )
    
    assert strategy.lookback_period == 20
    assert strategy.zscore_threshold == 2.0
    assert strategy.position_size == 0.1
    
    # Test position enum
    assert Position.LONG.value == "long"
    assert Position.SHORT.value == "short"
    assert Position.FLAT.value == "flat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])