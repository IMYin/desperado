# !/home/imyin/python_env/newspaper_python3/bin/python
# -*- coding: utf-8 -*-

"""
Create on 1/26/18 3:03 PM

@auther: imyin

@File: send_mail
"""

import smtplib
from email.header import Header
from email.mime.text import MIMEText

import constants as cons


def run_send(rate, main_coin, another_coin):
    mail_msg = "请注意,现由于ETH/BTC的兑换率达到了: {},已经由 {} 市场转换到 {} 市场进行交易." \
               "\n\n个别币种的价格可能不准确,请及时查看.".format(rate, main_coin, another_coin)
    message = MIMEText(mail_msg, u'plain', u'utf-8')
    message['From'] = Header(cons.FROM_ADDR, 'utf-8')
    message['To'] = Header(cons.TO_ADDR, 'utf-8')
    subject = '!!!Profit Trailer交易市场转换通知'
    message['Subject'] = Header(subject, 'utf-8')

    to_address = cons.TO_ADDR
    from_address = cons.FROM_ADDR
    password = cons.PASSWORD
    # Send the email via our own SMTP server.
    s = smtplib.SMTP_SSL(cons.SMTP_SERVER, 465)
    s.login(from_address, password)  # to login SMTP server.
    s.sendmail(from_address, to_address, message.as_string())
    s.quit()


if __name__ == '__main__':
    run_send('0.5', 'ETH', 'BTC')
