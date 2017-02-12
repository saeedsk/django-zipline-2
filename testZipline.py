# https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/blotter.py#L123
import pandas as pd
from zipline.finance.execution import (
    MarketOrder,
)

#####################################
from zipline.finance.trading import TradingEnvironment
from testfixtures import TempDirectory
import zipline.utils.factory as factory

with TempDirectory() as tempdir:
  env = TradingEnvironment()
  
  # save an asset
  df = pd.DataFrame(
      {  
        "sid":1,
        "exchange":'bla',
        "symbol":'bla',
        "asset_name":'bla',
      },
      index=[1],
  )
  env.write_data(equities=df)
  
  a1=env.asset_finder.retrieve_asset(sid=1)

  # prepare for data portal
  # from zipline/tests/test_finance.py#L238
  #  start_date=pd.Timestamp('2013-12-08 9:31AM', tz='UTC'),
  START_DATE = pd.Timestamp('2013-01-05', tz='utc')
  MID_DATE = pd.Timestamp('2013-01-06', tz='utc')
  END_DATE = pd.Timestamp('2013-01-07', tz='utc')
  sim_params = factory.create_simulation_parameters(
      start = START_DATE,
      end = END_DATE,
      data_frequency="daily"
  )
  
  days = sim_params.sessions
  
  # Use same sid as for assets above
  assets = {
      1: pd.DataFrame({
  	"open": [3.5] * len(days),
  	"high": [3.5] * len(days),
  	"low": [3.5] * len(days),
  	"close": [3.5] * len(days),
  	"volume": [10] * len(days),
  	"day": [day.value for day in days]
      }, index=days)
  }
  print("data: %s" % (assets))
  
  import os
  from zipline.data.us_equity_pricing import BcolzDailyBarReader, BcolzDailyBarWriter
  from zipline.utils.calendars import get_calendar
  trading_calendar=get_calendar("NYSE")
  
  path = os.path.join(tempdir.path, "testdata.bcolz")
  BcolzDailyBarWriter(path, trading_calendar, days[0], days[-1]).write(
      assets.items()
  )
  
  print("temp path: %s" % (path))
  equity_daily_reader = BcolzDailyBarReader(path)
  
  # try to use a data portal
  from zipline.data.data_portal import DataPortal
  dp = DataPortal(
    asset_finder=env.asset_finder,
    trading_calendar=trading_calendar,
    first_trading_day=equity_daily_reader.first_trading_day,
    equity_daily_reader=equity_daily_reader
  )
  from zipline._protocol import BarData
  
  # initialize blotter
  from zipline.finance.blotter import Blotter
  #from zipline.finance.slippage import FixedSlippage
  #slippage_func = FixedSlippage(spread=0.0)
  from zipline.finance.slippage import VolumeShareSlippage
  slippage_func = VolumeShareSlippage(volume_limit=1,price_impact=0)
  blotter = Blotter(data_frequency='daily',asset_finder=env.asset_finder, slippage_func=slippage_func)
  
  print("Start")
  blotter.set_date(MID_DATE)
  print(blotter.current_dt)
  
  print("Order a1 +10")
  o1=blotter.order(a1,10,MarketOrder())
  print("Open orders: %s" % (len(blotter.open_orders[a1])))
  
  print("Order a1 +10 and +10")
  o2=blotter.order(a1,10,MarketOrder())
  o3=blotter.order(a1,10,MarketOrder())
  print("Open orders: %s" % (len(blotter.open_orders[a1])))
  
  def simulation_dt_func(): return blotter.current_dt
  bd = BarData(data_portal=dp,simulation_dt_func=simulation_dt_func,data_frequency='daily',trading_calendar=trading_calendar)

  print("========================")
  print("use data portal to dequeue open orders: %s, %s" % (blotter.current_dt, simulation_dt_func()))
  new_transactions, new_commissions, closed_orders = blotter.get_transactions(bd)

  print("Closed orders: %s" % (len(closed_orders)))
  for order in closed_orders:
    print("Closed orders: %s" % (order))

  print("Transactions: %s" % (len(new_transactions)))
  for txn in new_transactions:
    print("Transactions: %s" % (txn.to_dict()))

  print("Commissions: %s" % (len(new_commissions)))
  for txn in new_commissions:
    print("Commissions: %s" % (txn))

  blotter.prune_orders(closed_orders)
  print("Open orders: %s" % (len(blotter.open_orders[a1])))
  print("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))

  print("========================")
  print("Cancel o2")
  blotter.cancel(o2)
  print("Open orders: %s" % (len(blotter.open_orders[a1])))
  print("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))
