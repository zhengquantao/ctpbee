from datetime import datetime

from ctpbee import CtpbeeApi, helper, CtpBee
from ctpbee.constant import ContractData, LogData, TickData, BarData, OrderType, Offset, OrderData, SharedData, \
    TradeData, PositionData, Direction, AccountData


class Demo(CtpbeeApi):
    instrument_set = ["rb2010.SHFE"]

    # 当前插件绑定的CtpBee的数据记录信息都在self.app.recorder下面

    def on_contract(self, contract: ContractData):
        """ 处理推送的合约信息 """
        # print(contract.local_symbol)
        if contract.local_symbol in self.instrument_set:
            self.app.subscribe(contract.local_symbol)
            print("back")

    def on_log(self, log: LogData):
        """ 处理日志信息 ,特殊需求才用到 """
        pass

    def on_tick(self, tick: TickData) -> None:
        """ 处理推送的tick """
        print(tick)
        pass

    def on_bar(self, bar: BarData) -> None:
        """ 处理ctpbee生成的bar """
        # 构建发单请求
        req = helper.generate_order_req_by_var(symbol=bar.symbol, exchange=bar.exchange, price=bar.high_price,
                                               direction=Direction.LONG, type=OrderType.LIMIT, volume=3,
                                               offset=Offset.OPEN)
        # 调用绑定的app进行发单
        id = self.action.sell(bar.high_price, 1, bar)
        print("返回id", id)

    def on_init(self, init):

        self.app.recorder.get_all_contracts()
        if init:
            print("初始化完成")

    def on_order(self, order: OrderData) -> None:
        """ 报单回报 """

    def on_trade(self, trade: TradeData) -> None:
        """ 成交回报 """

    def on_position(self, position: PositionData) -> None:
        """ 处理持仓回报 """

    def on_account(self, account: AccountData) -> None:
        """ 处理账户信息 """


def letsgo():
    app = CtpBee(name="demo", import_name=__name__)
    # 创建对象
    demo = Demo("test")
    # 添加对象, 你可以继承多个类 然后实例化不同的插件 再载入它, 这些都是极其自由化的操作
    app.add_extension(demo)
    app.config.from_json("config.json")
    app.start(log_output=True)
    # 单独开一个线程来进行查询持仓和账户信息


if __name__ == '__main__':
    letsgo()
