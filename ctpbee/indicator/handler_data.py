import os
import sys
import csv
import json
import time
import numpy as np
from datetime import datetime, date


class HandlerData:
    def __init__(self):
        self.count = 0                      # 数量
        self.ret_data = []                  # 总数据
        self.ret_open = []                  # 开盘价
        self.ret_low = []                   # 最低价
        self.ret_high = []                  # 最高价
        self.ret_date = []                  # 时间
        self.ret_close = []                 # 收盘价
        self.ret_volume = []                # 成交量
        self.open_file_name = None          # 文件名
        self.open_file_start = None         # 开始时间
        self.inited = False                 # 是否满足计算要求 self.count > self.min_inited 为True
        self.min_inited = 30                # 最低计算阀值
        self.max_array = 100                # 默认最大计算数组100

    def update_bar(self, datas, switch=False):
        """
        :param datas: 数据类型
                        [time, open, high, low, close, volume]
                        [1883823344, 22, 44, 55, 55, 6666]
        :param switch: 开关
        :return:
        """
        if not datas:
            raise Warning("type error or type is None")
        if isinstance(datas, dict):
            data = [datas["datetime"], datas["open_price"], datas["high_price"], datas["low_price"],
                    datas.get("close_price") or datas["last_price"],
                    1]
        else:
            try:
                datas = datas._to_dict()
            except:
                raise TypeError("只支持 dict和BarData这个两种数据")
            data = [datas["datetime"], datas["open_price"], datas["high_price"], datas["low_price"],
                    datas.get("close_price") or datas["last_price"],
                    1]
        if switch:

            if isinstance(data[0], datetime):
                data[0] = data[0].strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(data[0], date):
                data[0] = data[0].strftime('%Y-%m-%d')
            else:
                time_local = time.localtime(float(data[0]) / 1000)
                data[0] = time.strftime("%Y-%m-%d %H:%M:%S", time_local)

            if self.open_file_name.endswith(".csv"):
                with open(self.open_file_name, 'a+', newline='') as f:
                    w_data = csv.writer(f)
                    w_data.writerows(data)
            if self.open_file_name.endswith(".json"):
                with open(self.open_file_name, 'r') as jr:
                    r_json = json.loads(jr.read())
                    r_name = [name for name in r_json][0]
                    r_json[r_name].append(data)
                with open(self.open_file_name, 'w') as jw:
                    json.dump(r_json, jw)

            if self.open_file_name.endswith(".txt"):
                with open(self.open_file_name, 'a+') as t:
                    txt = "\n" + str(data).strip("[]")
                    t.write(txt)

        else:
            if self.count > self.max_array:
                self.ret_close = self.ret_close[-self.max_array:]
                self.ret_high = self.ret_high[-self.max_array:]
                self.ret_low = self.ret_low[-self.max_array:]
                self.ret_open = self.ret_open[-self.max_array:]
                self.ret_volume = self.ret_volume[-self.max_array:]
            self.count += 1
            if not self.inited and self.count >= self.min_inited:
                self.inited = True
            self.ret_close = np.append(self.ret_close, data[4])
            self.ret_high = np.append(self.ret_high, data[2])
            self.ret_low = np.append(self.ret_low, data[3])
            self.ret_open = np.append(self.ret_open, data[1])
            self.ret_volume = np.append(self.ret_volume, data[5])

    def save_file(self, data):
        """保存数据"""
        pass

    def path(self, file):
        if not file:
            raise FileExistsError("文件名不能为空")
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.join(modpath, file)
        self.open_file_name = datapath
        return datapath

    def data_columns(self, data, start_time=None, end_time=None):
        self.ret_data = data
        self.ret_volume = data[4]
        self.ret_open = data[0]
        self.ret_low = data[2]
        self.ret_high = data[1]
        self.ret_close = data[3]
        self.count = len(data[4])
        return self.ret_close

    def open_csv(self, file, start_time=None, end_time=None):
        """
        读取txt文件
            data_type:
                Date,Open,High,Low,Close,Volume
                '2019-01-07 00:00:00', 3831.0, 3847.0, 3831.0, 3840.0, 554
                '2019-01-08 00:00:00', 3841.0, 3841.0, 3833.0, 3836.0, 554
                ...
        :param file: 文件名
        :param start_time: 开始读取时间
        :param end_time: 结束时间
        :return: array对象
        """
        datapath = self.path(file)
        data = np.loadtxt(datapath, skiprows=2, dtype=float, delimiter=',', usecols=(1, 2, 3, 4, 5), unpack=True)
        ret_close = self.data_columns(data, start_time, end_time)
        return ret_close

    def open_json(self, file: str, start_time=None, end_time=None):
        """
        读取json文件
            data_type:
                {"zn1912.SHFE": [
                        ["2014-01-01", 18780.0, 18780.0, 18770.0, 18775.0, 266],
                        ["2014-01-02", 18775.0, 18780.0, 18770.0, 18770.0, 312],
                            ...
                        ]
                }
        :param file: 文件名
        :param start_time:
        :param end_time:
        :return:
        """
        datapath = self.path(file)
        data_str = open(datapath).read()
        data_loads = json.loads(data_str)
        for data_name, data_all in data_loads.items():
            data_lines = data_all
        datas = np.array(data_lines)
        data = np.array([datas[:, 1], datas[:, 2], datas[:, 3], datas[:, 4], datas[:, 5]], dtype=float)
        ret_close = self.data_columns(data, start_time, end_time)
        return ret_close

    def open_cache(self, data):
        """
        读取cache数据
        :param data:
            [[1883823344, 22, 44, 55, 55, 6666], [1883823345, 22, 44, 55, 55, 6666], ...]
        :return:
        """
        datas = np.array(data)
        data_array = np.array([datas[:, 1], datas[:, 2], datas[:, 3], datas[:, 4], datas[:, 5]], dtype=float)
        ret_close = self.data_columns(data_array)
        return ret_close
