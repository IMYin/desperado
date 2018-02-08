# !/home/imyin/python_env/newspaper_python3/bin/python
# -*- coding: utf-8 -*-

"""
Create on 1/21/18 2:38 PM

@auther: imyin

@File: do_logs
"""

import re
import subprocess
import sys
import time

import constants as cons
from utils import about_binance as ab
from utils.about_db import data_to_db as td


def filter_log(content):
    try:
        if 'Get order information' not in content:
            print(content)
            content = re.search('{.*}', content).group()
            content = re.sub('{', '', content)
            content = re.sub('}', '', content)
            content = re.sub('\"', '', content)
            before_dict = [item.split(cons.SPLIT_ITEM8) for item in content.split(cons.SPLIT_ITEM1)]
            content_dict = {item[0]: item[1] for item in before_dict}
            return content_dict
    except:
        pass


# price_change_percent = eth_btc['priceChangePercent']

def run(host_name, log_path, retry=10):
    command = 'ssh {} \"tail -f {}\"'.format(host_name, log_path)
    p_open = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    while True:
        line = p_open.stdout.readline().strip()
        information = filter_log(line.decode('utf-8'))
        if information and information.__len__() == 11:
            for i in range(retry):
                try:
                    price_eth_btc = ab.get_24_ticker('lastPrice')
                    break
                except:
                    pass
            symbol_now = information['symbol'][-3:]
            information['mainCoin'] = symbol_now
            if symbol_now == 'ETH':
                information['anotherPrice'] = str(round(float(information['price']) * float(price_eth_btc), 8))
            else:
                information['anotherPrice'] = str(round(float(information['price']) / float(price_eth_btc), 8))
            td(information)
            del (information)
        else:
            continue
        time.sleep(5)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
