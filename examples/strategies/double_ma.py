from ctpbee import CtpbeeApi, CtpBee
from ctpbee.constant import Offset, TradeData, Direction, ContractData
from ctpbee.indicator.ta_lib import ArrayManager
from ctpbee.indicator import IndicatorManager


class DoubleMaStrategy(CtpbeeApi):
    def __init__(self, name):
        super().__init__(name)
        self.manager = ArrayManager(100)
        self.instrument_set = ["rb2101.SHFE"]  # 这个里面的变量 如果你开启了行情分离选项， 当数据进来的时候会判断数据 只会把相应的行情送进来， 还要就是可以通过来订阅指定行情
        self.buy = 0
        self.sell = 0
        self.slow = 60
        self.fast = 30

    def on_trade(self, trade: TradeData):
        print(trade, "====")
        if trade.offset == Offset.OPEN:
            if trade.direction == Direction.LONG:
                self.buy += trade.volume
            else:
                self.sell += trade.volume
        else:
            if trade.direction == Direction.LONG:
                self.sell -= trade.volume
            else:
                self.buy -= trade.volume

    def on_bar(self, bar):
        """ """
        print(bar, "-------")
        self.manager.add_data(bar)
        if not self.manager.inited:
            return
        fast_avg = self.manager.sma(self.fast, array=True)
        slow_avg = self.manager.sma(self.slow, array=True)

        if slow_avg[-2] < fast_avg[-2] and slow_avg[-1] >= fast_avg[-1]:
            self.action.cover(bar.close_price, self.buy, bar)
            self.action.sell(bar.close_price, 3, bar)

        if fast_avg[-2] < slow_avg[-2] and fast_avg[-1] >= slow_avg[-1]:
            self.action.sell(bar.close_price, self.sell, bar)
            self.action.buy(bar.close_price, 3, bar)

    def on_tick(self, tick):
        pass

    def on_init(self, init: bool):
        print("初始化成功了, 这里可能会触发两次哦")

    def on_contract(self, contract: ContractData) -> None:
        # print(contract)
        if contract.local_symbol in ["rb2205.SHFE", "ag2306P4600.SHFE", "al2305C15200.SHFE"]:
            self.action.subscribe(contract.local_symbol)  # 订阅行情
            print("合约乘数: ", contract.size)


class DoubleMaStrategyDemo(CtpbeeApi):
    def __init__(self, name):
        super().__init__(name)
        self.manager = IndicatorManager()
        self.instrument_set = ["rb2101.SHFE"]  # 这个里面的变量 如果你开启了行情分离选项， 当数据进来的时候会判断数据 只会把相应的行情送进来， 还要就是可以通过来订阅指定行情
        self.buy = 0
        self.sell = 0
        self.slow = 10
        self.fast = 15

    def on_trade(self, trade: TradeData):
        print(trade, "====")
        if trade.offset == Offset.OPEN:
            if trade.direction == Direction.LONG:
                self.buy += trade.volume
            else:
                self.sell += trade.volume
        else:
            if trade.direction == Direction.LONG:
                self.sell -= trade.volume
            else:
                self.buy -= trade.volume

    def on_bar(self, bar):
        """ """
        self.manager.add_bar(bar)
        print('---', self.manager.inited, bar)
        if not self.manager.inited:
            return

        fast_avg = self.manager.sma(self.fast)
        slow_avg = self.manager.sma(self.slow)

        print("fast", fast_avg)
        print("slow", slow_avg)
        if slow_avg[-2] < fast_avg[-2] and slow_avg[-1] >= fast_avg[-1]:
            self.action.cover(bar.close_price, self.buy, bar)
            self.action.sell(bar.close_price, 3, bar)

        if fast_avg[-2] < slow_avg[-2] and fast_avg[-1] >= slow_avg[-1]:
            self.action.sell(bar.close_price, self.sell, bar)
            self.action.buy(bar.close_price, 3, bar)

    def on_tick(self, tick):
        self.manager.add_bar(tick)
        if not self.manager.inited:
            return
        fast_avg = self.manager.sma(self.fast)
        slow_avg = self.manager.sma(self.slow)
        print("tick==", self.manager.inited, tick)

        print("fast", fast_avg)
        print("slow", slow_avg)

    def on_init(self, init: bool):
        print("初始化成功了, 这里可能会触发两次哦")

    def on_contract(self, contract: ContractData) -> None:
        # print(contract)
        if contract.local_symbol in ["rb2205.SHFE", "ag2306P4600.SHFE", "al2305C15200.SHFE"]:
            self.action.subscribe(contract.local_symbol)  # 订阅行情
            print("合约乘数: ", contract.size)


if __name__ == '__main__':
    app = CtpBee("doublema", __name__, refresh=True)
    app.config.from_mapping({
        "CONNECT_INFO": {
            "userid": "089131",
            "password": "350888",
            "brokerid": "9999",
            "md_address": "tcp://180.168.146.187:10131",
            "td_address": "tcp://180.168.146.187:10130",
            "product_info": "",
            "appid": "simnow_client_test",
            "auth_code": "0000000000000000"
        },
        "INTERFACE": "ctp",  # 接口声明
        "TD_FUNC": True,  # 开启交易功能
        "MD_FUNC": True,
        "XMIN": [1, 3]
    })
    strategy = DoubleMaStrategyDemo("doublema")
    app.add_extension(strategy)
    app.start()
