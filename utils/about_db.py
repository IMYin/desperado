# !/home/imyin/python_env/newspaper_python3/bin/python
# -*- coding: utf-8 -*-

"""
Create on 1/21/18 2:31 PM

@auther: imyin

@File: about_db
"""

import pymysql

import constants as cons


def conn_mysql():
    """
    To connect the mysql.
    Attentions: charset is a important parameter.

    :return: connection
    """
    connection = pymysql.connect(host=cons.mysql_host,
                                 user=cons.mysql_user,
                                 password=cons.mysql_passwd,
                                 db=cons.db_name,
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def data_to_db(contents):
    connection = conn_mysql()
    try:
        with connection.cursor() as cursor:
            sql = cons.insert_db.format(cons.coin_table_name)
            cursor.execute(sql, (contents['mainCoin'],
                                 contents['symbol'],
                                 contents['transactTime'],
                                 contents['price'],
                                 contents['anotherPrice'],
                                 contents['origQty'],
                                 contents['executedQty'],
                                 contents['status'],
                                 contents['side']))
        connection.commit()
    finally:
        connection.close()
