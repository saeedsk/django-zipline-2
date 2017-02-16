from __future__ import unicode_literals
from .util import md5_wrap
from zipline.finance.execution import (
#    LimitOrder,
    MarketOrder,
#    StopLimitOrder,
#    StopOrder,
)
from django.db import connection

# Django Logging
# https://docs.djangoproject.com/en/1.10/topics/logging/
import logging
logger = logging.getLogger(__name__)

import json
from ...matcher import factory as mmm_factory, Matcher as mmm_Matcher
from functools import reduce

from numpy import concatenate
import pandas as pd

class ZlModel:
    md5 = None
    zl_open       = []
    zl_closed     = []
    zl_txns       = []
    zl_open_keyed = {}
    zl_closed_keyed = {}
    fills={}
    orders={}
    assets={}
    zl_unused = {}

    @staticmethod
    def clear():
      ZlModel.md5 = None
      ZlModel.zl_open       = []
      ZlModel.zl_closed     = []
      ZlModel.zl_txns       = []
      ZlModel.zl_open_keyed = {}
      ZlModel.zl_closed_keyed = {}
      ZlModel.fills={}
      ZlModel.orders={}
      ZlModel.assets={}
      ZlModel.zl_unused = {}

    @staticmethod
    def add_asset(asset):
      #print("adding asset",asset,asset.id)
      ZlModel.assets[asset.id]=asset.to_dict()

    # cannot use typehinting as
    # def add_fill(fill: Fill): ...
    # because then I would need to import .fill in this file
    # and fill.py already has an import.zlmodel
    # so this will become a cyclic dependency
    @staticmethod
    def add_fill(fill):
      #print("Adding fill: %s" % fill)
      if fill.asset.id not in ZlModel.fills:
        ZlModel.fills[fill.asset.id]={}

      ZlModel.fills[fill.asset.id][fill.id]={
        "close": fill.fill_price,
        "volume": fill.fill_qty,
        "dt": pd.Timestamp(fill.pub_date,tz='utc')
      }

    @staticmethod
    def fills_as_dict_df():
      # Copy keys to a new dictionary (Python)
      # http://stackoverflow.com/a/7369284/4126114
      fills2=dict.fromkeys(ZlModel.fills.keys(),{})

      for sid in ZlModel.fills:
        fills2[sid] = pd.DataFrame({})
        sub = ZlModel.fills[sid].values()
        fills2[sid]["close"]=[y["close"] for y in sub]
        fills2[sid]["volume"]=[y["volume"] for y in sub]
        fills2[sid]["dt"]=[y["dt"] for y in sub]
        fills2[sid]=fills2[sid].set_index("dt")
      return fills2

    @staticmethod
    def add_order(order):
      if order.asset.id not in ZlModel.orders:
        ZlModel.orders[order.asset.id]={}

      ZlModel.orders[order.asset.id][order.id] = {
        "dt": order.pub_date,
        "asset": order.asset.id,
        "amount": order.amount,
        "style": MarketOrder()
      }

    @staticmethod
    def delete_asset(asset):
      ZlModel.assets.pop(asset.id, None)

    @staticmethod
    def delete_fill(fill):
      # How to remove a key from a python dictionary
      # http://stackoverflow.com/questions/11277432/ddg#11277439
      ZlModel.fills[fill.asset.id].pop(fill.id, None)
      if not any(ZlModel.fills[fill.asset.id]):
        ZlModel.fills.pop(fill.asset.id, None)

    @staticmethod
    def delete_order(order):
      # How to remove a key from a python dictionary
      # http://stackoverflow.com/questions/11277432/ddg#11277439
      ZlModel.orders.pop(order.id, None)

    @staticmethod
    def db_ready():
      tables = connection.introspection.table_names()
      isready = "zipline_app_fill" in tables
      if not isready:
        logger.debug("db tables not available .. skipping zlmodel init")
      return isready

    @staticmethod
    def init(fills, orders, assets):
      if not ZlModel.db_ready():
        return

      for fill in fills:
        ZlModel.add_fill(fill)
      for order in orders:
        ZlModel.add_order(order)
      for asset in assets:
        ZlModel.add_asset(asset)

    @staticmethod
    def update():
      if not ZlModel.db_ready():
        return

      md5_orders = []
      for sid,o1 in ZlModel.orders.items():
        for oid,o2 in o1.items():
          # No need for "account" here
          # since orders for 2 different accounts will have 2 different IDs anyway.
          # Also, order_text is not passed to the engine anyway
          md5_orders.append(
            "%s, %s, %s, %s" % (
              o2["dt"],
              sid,
              o2["amount"],
              "MarketOrder" # TODO get type when I support other types (in case order type was changed)
            )
          )

      md5_fills = []
      for sid, f1 in ZlModel.fills.items():
        for dt, fill in f1.items():
          md5_fills.append(
            "%s, %s, %s, %s" % (
              sid,
              fill["volume"],
              fill["close"],
              dt
            )
          )
          
      md5 = md5_wrap(json.dumps({
        "fills" : md5_fills,
        "orders": md5_orders,
        "assets": ZlModel.assets,
      }))

      if ZlModel.md5==md5:
        logger.debug("Model unchanged .. not rerunning engine: "+md5)
        return

      logger.debug("Run matching engine: "+md5)

      matcher = mmm_Matcher()

      all_closed, all_txns, open_orders, ZlModel.zl_unused, ZlModel.all_minutes = mmm_factory(
        matcher,
        ZlModel.fills_as_dict_df(),
        ZlModel.orders,
        ZlModel.assets
      )

      ZlModel.zl_open = reduce(
        lambda a, b: concatenate((a,b)),
        [v for k,v in open_orders.items()],
        list()
      )
      ZlModel.zl_closed = all_closed
      ZlModel.zl_txns = [txn.to_dict() for txn in all_txns]
      ZlModel.zl_open_keyed = {v.id: v for v in ZlModel.zl_open}
      ZlModel.zl_closed_keyed = {v.id: v for v in ZlModel.zl_closed}

      # save md5 at the end to ensure re-run if error occured
      ZlModel.md5=md5