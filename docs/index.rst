QuantTradingPro Documentation
===============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tutorials/getting_started
   api/modules
   faq/faq

Introduction
------------

QuantTradingPro is a professional quantitative trading library for Python.

Features
--------

* Multiple trading strategies (mean reversion, trend following, momentum)
* Risk management and position sizing
* Data fetching from multiple sources
* Backtesting framework
* Machine learning integration

Quick Start
-----------

.. code-block:: python

   pip install quanttradingpro

   from quanttradingpro import MeanReversionStrategy
   
   strategy = MeanReversionStrategy(
       lookback_period=20,
       zscore_threshold=2.0
   )

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`