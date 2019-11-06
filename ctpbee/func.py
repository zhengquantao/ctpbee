"""

面向用户的函数 ,提供极其便捷的体验

"""
import logging
import os
from datetime import time, datetime
from inspect import isfunction
from multiprocessing import Process
from time import sleep
from typing import Text, Any, List

from ctpbee.constant import \
    (OrderRequest, CancelRequest, Direction, Exchange,
     Offset, OrderType, AccountRegisterRequest, AccountBanlanceRequest, TransferRequest, TransferSerialRequest,
     MarketDataRequest)
from ctpbee.context import current_app
from ctpbee.context import get_app
from ctpbee.exceptions import TraderError, MarketError
from ctpbee.signals import send_monitor, cancel_monitor


def send_order(order_req: OrderRequest, app_name: str = "current_app"):
    """ 发单 """
    if app_name == "current_app":
        app = current_app
    else:
        app = get_app(app_name)
    if not app.config.get("TD_FUNC"):
        raise TraderError(message="交易功能未开启", args=("交易功能未开启",))
    send_monitor.send(order_req)
    return app.trader.send_order(order_req)


def cancel_order(cancel_req: CancelRequest, app_name: str = "current_app"):
    """ 撤单 """
    if app_name == "current_app":
        app = current_app
    else:
        app = get_app(app_name)
    if not app.config.get("TD_FUNC"):
        raise TraderError(message="交易功能未开启", args=("交易功能未开启",))
    cancel_monitor.send(cancel_req)
    app.trader.cancel_order(cancel_req)


def subscribe(symbol: Text, app_name: str = "current_app") -> None:
    """订阅"""
    if app_name == "current_app":
        app = current_app
    else:
        app = get_app(app_name)
    if not app.config.get("MD_FUNC"):
        raise MarketError(message="行情功能未开启, 无法进行订阅")
    app.market.subscribe(symbol)


def query_func(type: Text, app_name: str = "current_app") -> None:
    """ 查询持仓或者账户 """
    if app_name == "current_app":
        app = current_app
    else:
        app = get_app(app_name)
    if not app.config.get("TD_FUNC"):
        raise TraderError(message="交易功能未开启", args=("交易功能未开启",))
    if type == "position":
        app.trader.query_position()
    if type == "account":
        app.trader.query_account()


class Helper():
    """ 工具函数 帮助你快速构建查询请求 """
    direction_map = {
        "LONG": Direction.LONG,
        "SHORT": Direction.SHORT,
    }
    exchange_map = {
        "SHFE": Exchange.SHFE,
        "INE": Exchange.INE,
        "CZCE": Exchange.CZCE,
        "CFFEX": Exchange.CFFEX,
        "DCE": Exchange.DCE,
        "SSE": Exchange.SSE,
        "SZSE": Exchange.SZSE,
        "SGE": Exchange.SGE
    }

    offset_map = {
        "CLOSE": Offset.CLOSE,
        "OPEN": Offset.OPEN,
        "CLOSETODAY": Offset.CLOSETODAY,
        "CLOSEYESTERDAY": Offset.CLOSEYESTERDAY
    }

    price_type_map = {
        "MARKET": OrderType.MARKET,
        "STOP": OrderType.STOP,
        "FAK": OrderType.FAK,
        "LIMIT": OrderType.LIMIT,
        "FOK": OrderType.FOK
    }

    @classmethod
    def generate_order_req_by_str(cls, symbol: str, exchange: str, direction: str, offset: str, type: str, volume,
                                  price: float):
        """ 手动构造发单请求"""
        if "." in symbol:
            symbol = symbol.split(".")[0]

        return OrderRequest(exchange=cls.exchange_map.get(exchange.upper()), symbol=symbol,
                            direction=cls.direction_map.get(direction.upper()),
                            offset=cls.offset_map.get(offset.upper()), type=cls.price_type_map.get(type.upper()),
                            volume=volume, price=price)

    @classmethod
    def generate_order_req_by_var(cls, symbol: str, exchange: Exchange, direction: Direction, offset: Offset,
                                  type: OrderType, volume, price: float):
        if "." in symbol:
            symbol = symbol.split(".")[0]
        return OrderRequest(symbol=symbol, exchange=exchange, direction=direction, offset=offset, type=type,
                            volume=volume, price=price)

    @classmethod
    def generate_cancel_req_by_str(cls, symbol: str, exchange: str, order_id: str):
        if "." in symbol:
            symbol = symbol.split(".")[0]
        return CancelRequest(symbol=symbol, exchange=cls.exchange_map.get(exchange), order_id=order_id)

    @classmethod
    def generate_cancel_req_by_var(cls, symbol: str, exchange: Exchange, order_id: str):
        if "." in symbol:
            symbol = symbol.split(".")[0]
        return CancelRequest(symbol=symbol, exchange=exchange, order_id=order_id)

    @classmethod
    def generate_ac_register_req(cls, bank_id, currency_id="CNY"):

        return AccountRegisterRequest(bank_id=bank_id, currency_id=currency_id)

    @classmethod
    def generate_ac_banlance_req(cls, bank_id, bank_account, bank_password,
                                 currency_id="CNY"):
        return AccountBanlanceRequest(bank_id=bank_id, bank_account=bank_account, bank_password=bank_password,
                                      currency_id=currency_id)

    @classmethod
    def generate_transfer_request(cls, bank_id, bank_account, bank_password,
                                  trade_account, currency_id="CNY"):
        return TransferRequest(bank_id=bank_id, bank_account=bank_account, band_password=bank_password,
                               currency_id=currency_id,
                               trade_account=trade_account)

    @classmethod
    def generate_transfer_serial_req(cls, bank_id, currency_id="CNY"):
        return TransferSerialRequest(bank_id=bank_id, currency_id=currency_id)

    @classmethod
    def generate_market_request(cls, symbol: str, exchange: Any):
        """ 生成市场数据请求 """
        if "." in symbol:
            symbol = symbol.split(".")[1]
        if isinstance(exchange, Exchange):
            exchange = exchange.value
        return MarketDataRequest(symbol=symbol, exchange=exchange)


helper = Helper()


def auth_time(data_time: time):
    """
    校验时间tick或者bar的时间合不合法
    for example:
        data_time = tick.datetime.time()
    """
    if not isinstance(data_time, time):
        raise TypeError("参数类型错误, 期望为datetime.time}")
    DAY_START = time(9, 0)  # 日盘启动和停止时间
    DAY_END = time(15, 0)
    NIGHT_START = time(21, 0)
    NIGHT_END = time(2, 30)
    if data_time <= DAY_END and data_time >= DAY_START:
        return True
    if data_time >= NIGHT_START:
        return True
    if data_time <= NIGHT_END:
        return True
    return False


class Hickey(object):
    """ ctpbee进程调度 """

    logger = logging.getLogger("ctpbee")

    def __init__(self):
        self.names = []

    def auth_time(self, current: datetime):
        from datetime import time
        DAY_START = time(8, 57)  # 日盘启动和停止时间
        DAY_END = time(15, 5)
        NIGHT_START = time(20, 57)  # 夜盘启动和停止时间
        NIGHT_END = time(2, 35)
        if ((current.today().weekday() == 6) or
                (current.today().weekday() == 5 and current.time() > NIGHT_END) or
                (current.today().weekday() == 0 and current.time() < DAY_START)):
            return False
        if current.time() <= DAY_END and current.time() >= DAY_START:
            return True
        if current.time() >= NIGHT_START:
            return True
        if current.time() <= NIGHT_END:
            return True
        return False

    def run_all_app(self, app_func):
        from ctpbee.app import CtpBee
        apps = app_func()
        if isinstance(apps, CtpBee):
            if not apps.active:
                apps.start()
            else:
                raise ValueError("你选择的app已经在函数中启动")

        elif isinstance(apps, List) and isinstance(apps[0], CtpBee):
            for app in apps:
                if app.name not in self.names and not app.active:
                    app.start()
                    self.names.append(app.name)
                else:
                    continue
        else:
            raise ValueError("你传入的创建的func无法创建CtpBee变量, 请检查返回值")

    def start_all(self, app_func):
        """ 开始进程管理 """
        print("""
        Ctpbee 7*24 Manager started !
        Warning: program will automatic start at trade time ....
        Hope you will have a  good profit ^_^
        """)
        if not isfunction(app_func):
            raise TypeError(f"请检查你传入的app_func是否是创建app的函数,  而不是{type(app_func)}")
        p = None
        while True:
            """ """
            current = datetime.now()
            status = self.auth_time(current)
            if p is None and status == True:
                p = Process(target=self.run_all_app, args=(app_func,))
                p.start()
                self.logger.info("启动程序")
            if not status and p is not None:
                self.logger.info("查杀子进程")
                import os
                import platform
                if platform.uname().system == "Windows":
                    os.popen('taskkill /F /pid ' + str(p.pid))
                else:
                    import signal
                    os.kill(p.pid, signal.SIGKILL)
                self.logger.info("关闭成功")
                p = None
            sleep(30)

    def __repr__(self):
        return "ctpbee 7*24 manager "


hickey = Hickey()


class RLock:
    def __init__(self, name, second=10):
        """ 创建一个新锁 """
        self._start = datetime.now().timestamp()
        self._end = self._start + second

    def release(self):
        pass


def get_ctpbee_path():
    """ 获取ctpbee的路径默认路径 """
    import os
    home_path = os.environ['HOME']
    ctpbee_path = os.path.join(home_path, ".ctpbee")
    if not os.path.isdir(ctpbee_path):
        os.mkdir(ctpbee_path)
    return ctpbee_path
