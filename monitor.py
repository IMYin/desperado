# !/home/imyin/python_env/newspaper_python3/bin/python
# -*- coding: utf-8 -*-

"""
Create on 1/21/18 9:34 PM

@auther: imyin

@File: monitor
"""
import os
import re
import subprocess
import sys
import time
from datetime import datetime

import pandas as pd

import constants as cons
from Log.JobLogging import JobLogging
from send_mail import run_send
from utils import about_binance as ab
from utils import about_db as ad

config_path = sys.argv[1]
rate_trigger = sys.argv[2]


class Logging(object):
    # initial log
    def __init__(self, log_lev='INFO'):
        date_today = datetime.now().date()
        self.log_name = os.path.splitext(os.path.split(sys.argv[0])[1])[0]
        log_dir = cons.TASK_LOG_PATH
        self.today = date_today.strftime("%Y-%m-%d")
        if not os.path.isdir(log_dir):
            try:
                os.makedirs(log_dir)
            except:
                pass
        my_log = JobLogging(self.log_name, log_dir)
        my_log.set_level(log_lev)
        self.log = my_log.get_logger()
        self.log.info("today is {}, logs created...".format(self.today))


logs = Logging()


def move_exchange(main_coin, another_coin):
    notOk = config_path + '.notOk'
    bak = config_path + '.bak'
    prices = price_dict(main_coin)
    with open(notOk, mode='w') as f:
        for line in open(config_path):
            if not re.search('cutLine', line):
                f.write(line)
            else:
                f.write('#cutLine\n')
                break
    with open(bak, mode='w') as f:
        for line in open(config_path):
            f.write(line)
        if prices:
            for k, v in get_init_price(prices).items():
                f.write('{}_bought_price = {}\n'.format(k, v))
    with open(config_path, 'w') as f:
        for line in open(notOk):
            f.write(line.replace(main_coin, another_coin))
        if prices:
            for item in fill_words(main_coin, prices):
                f.write(item + '\n')
        f.write('\nBTCETH_trading_enabled = false\nETHBTC_trading_enabled = false')
    logs.log.info('File changed for {}!!!!'.format(another_coin))
    move_data_mysql()
    # clear_log(cons.TRADING_LOG_PATH)  # 不需要清除日志


def get_init_price(price_info):
    connection = ad.conn_mysql()
    init_price = {}
    try:
        with connection.cursor() as cursor:
            for symbol, another_price in price_info.items():
                sql = cons.get_init_price.format(cons.coin_table_name, symbol, another_price)
                x = cursor.execute(sql)
                result = cursor.fetchone()
                init_price[symbol] = result['price']
            return init_price
    finally:
        connection.close()


def _get_price_of_pairs(main_coin):
    connection = ad.conn_mysql()
    try:
        with connection.cursor() as cursor:
            sql = cons.get_all_data.format(cons.coin_table_name, main_coin)
            x = cursor.execute(sql)
            result = cursor.fetchmany(x)
            return result
    except Exception as e:
        print('No data in table.')
        return
    finally:
        connection.close()


def move_data_mysql():
    connection = ad.conn_mysql()
    try:
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE {} AS SELECT * FROM {}"
                           .format('bak_' + datetime.now().strftime('%Y%m%d%H%M%S'), cons.coin_table_name))
            cursor.execute('DELETE FROM {}'.format(cons.coin_table_name))
            connection.commit()
    finally:
        connection.close()


def clear_log(log_path):
    clear_command = 'echo > {}'.format(log_path)
    subprocess.Popen(clear_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)


def confirm_price(coin_pair):
    info_length = len(coin_pair)
    bought_price = coin_pair[coin_pair['side'] == 'BUY'].loc[:, 'anotherPrice'].values
    mark, buy_qty, sell_qty = -1, 0, 0
    for index, (_, row) in enumerate(coin_pair.iterrows()):
        if index == 0:
            if row['side'] == 'SELL':
                buy_qty = float(row['origQty'])
                sell_qty += float(row['executedQty'])
            else:
                mark += 1
                if 0 != float(row['executedQty']):
                    buy_qty = float(row['executedQty'])
                elif 0 == float(row['executedQty']) and len(bought_price) == 1:
                    return
                else:
                    buy_qty = 1e-08
                    mark += 1
        else:
            if row['side'] == 'SELL':
                sell_qty += float(row['executedQty'])
            else:
                if float(row['executedQty']) != 0 and (buy_qty - sell_qty) / buy_qty < 0.01:
                    mark += 1
                    sell_qty = 0
                    if 0 != float(row['executedQty']):  # 如果交易失败,则按照成交数量计算
                        buy_qty = float(row['executedQty'])
                    else:
                        # 考虑到钱包已无余额,但最后一笔买入成交数为0的情况
                        if index != info_length - 1:
                            buy_qty = 1e-08
                            mark += 1
                        else:
                            return
                elif float(row['executedQty']) == 0:
                    mark += 1
                else:
                    buy_qty += float(row['executedQty'])
    if (buy_qty - sell_qty) / buy_qty > 0.01:
        if mark != -1:
            if bought_price.__len__() != 0:
                return bought_price[mark]
            else:
                return
        else:
            return coin_pair.iloc[0].anotherPrice
    else:
        return


def price_dict(main_coin):
    global valid_qty
    data = _get_price_of_pairs(main_coin)
    if data:
        df = pd.DataFrame(data, columns=['id',
                                         'mainCoin',
                                         'symbol',
                                         'transactTime',
                                         'price',
                                         'anotherPrice',
                                         'origQty',
                                         'executedQty',
                                         'status',
                                         'side', ])
        all_pairs = pd.unique(df['symbol'])
        price_info = {}
        for pair in all_pairs:
            to_do = df[df['symbol'] == pair]
            price = confirm_price(to_do)
            if price:
                logs.log.info("Calculate the another coin\'s price is {}".format(price))
                price_info[pair] = price
        return price_info
    else:
        return


def fill_words(main_coin, price_info):
    if main_coin == 'ETH':
        return ['{}_bought_price = {}'.format(k.replace('ETH', 'BTC'), v) for k, v in price_info.items()]
    else:
        return ['{}_bought_price = {}'.format(k.replace('BTC', 'ETH'), v) for k, v in price_info.items()]


def run(retry=10):
    global rate_now
    while True:
        for i in range(retry):
            try:
                rate_now = ab.get_24_ticker('priceChangePercent')
                break
            except:
                pass
        main_coin = ab.get_main_coin(config_path)
        if float(rate_now) > float(rate_trigger) and main_coin == 'ETH':
            logs.log.info(
                'The ETH/BTC rate is {} now, need to change to {} market to exchange...'.format(rate_now, 'BTC'))
            move_exchange(main_coin, 'BTC')
            run_send(rate_now, main_coin, 'BTC')
            logs.log.info('Change market OK!!!')
        elif float(rate_now) < -float(rate_trigger) and main_coin == 'BTC':
            logs.log.info(
                'The ETH/BTC rate is {} now, need to change to {} market to exchange...'.format(rate_now, 'ETH'))
            move_exchange(main_coin, 'ETH')
            run_send(rate_now, main_coin, 'ETH')
            logs.log.info('Change market OK!!!')
        else:
            logs.log.info(
                'The ETH/BTC rate is {} now, don\'t need to change market...'.format(rate_now, 'BTC'))
            pass
        time.sleep(cons.monitoring_cycle)


if __name__ == '__main__':
    run()
