"""
    当前回测示例
    1.当前数据基于rq进行下载的
    2.首先你需要调用get_data 来获得rq的数据 ，然后save_to_json保存到 json文件中去，主要在此过程中你需要手动对数据加入symbol等
    3.然后通过load_data函数重复调用数据
    4.调用run_main进行回测

    当前的strategy是借助vnpy的 ArrayManager . 你需要对此实现一些额外的安装操作

    需要额外安装的包
    ta-lib,  rqdatac( 后面需要被取代  ？？ Maybe use quantdata )

    目前暂时不够完善   ---> hope it will be a  very fancy framework

    written by somewheve  2019-9-30 08:43

"""

import json
from datetime import datetime, date

from ctpbee import LooperApi, Vessel
from ctpbee.constant import Direction
from ctpbee.indicator import Interface


# def get_data(start, end, symbol, exchange, level):
#     """ using rqdatac to make an example """
#     import rqdatac as rq
#     from rqdatac import get_price, id_convert
#     username = "license"
#     password = "NK-Ci7vnLsRiPPWYwxvvPYdYM90vxN60qUB5tVac2mQuvZ8f9Mq8K_nnUqVspOpi4BLTkSLgq8OQFpOOj7L" \
#                "t7AbdBZEBqRK74fIJH5vsaAfFQgl-tuB8l03axrW8cyN6-nBUho_6Y5VCRI63Mx_PN54nsQOpc1psIGEz" \
#                "gND8c6Y=bqMVlABkpSlrDNk4DgG-1QXNknJtk0Kkw2axvFDa0E_XPMqOcBxifuRa_DFI2svseXU-8A" \
#                "eLjchnTkeuvQkKh6nrfehVDiXjoMeq5sXgqpbgFAd4A5j2B1a0gpE3cb5kXb42n13fGwFaGris" \
#                "8-eKzz_jncvuAamkJEQQV0aLdiw="
#     host = "rqdatad-pro.ricequant.com"
#     port = 16011
#     rq.init(username, password, (host, port))
#     symbol_rq = id_convert(symbol)
#     data = get_price(symbol_rq, start_date=start, end_date=end, frequency=level, fields=None,
#                      adjust_type='pre', skip_suspended=False, market='cn', expect_df=False)
#     origin = data.to_dict(orient='records')
#     result = []
#     for x in origin:
#         do = {}
#         do['open_price'] = x['open']
#         do['low_price'] = x['low']
#         do['high_price'] = x['high']
#         do['close_price'] = x['close']
#         do['datetime'] = datetime.strptime(str(x['trading_date']), "%Y-%m-%d %H:%M:%S")
#         do['symbol'] = symbol
#         do['local_symbol'] = symbol + "." + exchange
#         do['exchange'] = exchange
#         result.append(do)
#     return result


def get_a_strategy():

    class DoubleMaStrategy(LooperApi):

        allow_max_price = 5000  # 设置价格上限 当价格达到这个就卖出 防止突然跌 止盈
        allow_low_price = 2000  # 设置价格下限 当价格低出这里就卖 防止巨亏 止损

        def __init__(self, name):
            super().__init__(name)
            self.count = 1
            self.api = Interface()
            self.api.open_json("zn1912.SHFE.json")
            self.pos = 0

        def on_bar(self, bar):
            # todo: 均线 和 MACD 和 BOLL 结合使用
            """ """
            am = self.api
            am.add_bar(bar)
            # 收盘
            close = am.close
            # 压力 平均 支撑
            top, middle, bottom = am.boll()
            # DIF DEA DIF-DEA
            macd, signal, histo = am.macd()

            if self.allow_max_price <= close[-1] and self.pos > 0:
                self.action.sell(bar.close_price, self.pos, bar)

            if self.allow_low_price >= close[-1] and self.pos > 0:
                self.action.sell(bar.close_price, self.pos, bar)
            # 金叉做多 和 均线>平均
            if histo[-1] > 0 and close[-1] > middle[-1]:
                if self.pos == 0:
                    self.action.buy(bar.close_price, 1, bar)
                # 反向进行开仓
                elif self.pos < 0:
                    self.action.cover(bar.close_price, 1, bar)
                    self.action.buy(bar.close_price, 1, bar)
            # 死叉做空
            elif histo[-1] < 0:
                if self.pos == 0:
                    pass
                # 反向进行开仓
                elif self.pos > 0:
                    self.action.sell(bar.close_price, 1, bar)
                    self.action.short(bar.close_price, 1, bar)

        def on_trade(self, trade):
            if trade.direction == Direction.LONG:
                self.pos += trade.volume
            else:
                self.pos -= trade.volume

        def init_params(self, data):
            """"""
            # print("我在设置策略参数")

    return DoubleMaStrategy("double_ma")


def save_data_json(data):
    result = {"result": data}

    class CJsonEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(obj, date):
                return obj.strftime('%Y-%m-%d')
            else:
                return json.JSONEncoder.default(self, obj)

    with open("data.json", "w") as f:
        json.dump(result, f, cls=CJsonEncoder)


def load_data():
    with open("data.json", "r") as f:
        data = json.load(f)
    return data.get("result")


def run_main(data):
    vessel = Vessel()
    vessel.add_data(data)
    stra = get_a_strategy()
    vessel.add_strategy(stra)
    vessel.set_params({"looper":
                           {"initial_capital": 100000,
                            "commission": 0.005,
                            "deal_pattern": "price",
                            "size_map": {"ag1912.SHFE": 15},
                            "today_commission": 0.005,
                            "yesterday_commission": 0.02,
                            "close_commission": 0.005,
                            "slippage_sell": 0,
                            "slippage_cover": 0,
                            "slippage_buy": 0,
                            "slippage_short": 0,
                            "close_pattern": "yesterday",
                            },
                       "strategy": {}
                       })
    vessel.run()
    from pprint import pprint
    result = vessel.get_result()
    pprint(result)


if __name__ == '__main__':
    # data = get_data(start="2019-1-5", end="2019-9-1", symbol="ag1912", exchange="SHFE", level="15m")
    # save_data_json(data)
    data = load_data()
    for x in data:
        x['datetime'] = datetime.strptime(str(x['datetime']), "%Y-%m-%d %H:%M:%S")
    run_main(data)
