# !/home/imyin/python_env/newspaper_python3/bin/python
# -*- coding: utf-8 -*-

"""
Create on 1/21/18 4:38 PM

@auther: imyin

@File: about_web
"""
import re

from binance.client import Client

import constants as cons


def get_24_ticker(info_title):
    client = Client(cons.binance_api_key, cons.binance_api_secret)
    eth_btc = client.get_ticker()[0]
    return eth_btc[info_title]


def get_main_coin(config_path):
    global matched
    for line in open(config_path, mode='r'):
        if re.match('MARKET.*', line):
            matched = line.strip()
            break
    return matched[-3:]
