# 这个策略是根据15分钟

import random
from notify import NotifyService
from binanceApi import *
from util import *

try:
    import thread
except ImportError:
    import _thread as thread


def dealMsg(message):
    if message['e'] == "ORDER_TRADE_UPDATE" and message['o']['x'] == "TRADE" and message['o']['X'] == "FILLED" and \
            (message['o']['ot'] == "STOP_MARKET" or message['o']['ot'] == "LIMIT"):
        def run():
            try:
                orderId = globalVar['orderMap'][message['o']['i']]
                deleteOrder(symbol, orderId)
                globalVar['orderMap'].pop(orderId)
            except Exception as e:
                print(e)
            globalVar['orderMap'].pop(message['o']['i'])
            if message['o']['ot'] == "STOP_MARKET" or message['o']['ot'] == "LIMIT":
                if message['o']['ot'] == "STOP_MARKET":
                    globalVar['loss_count'] += 1
                elif message['o']['ot'] == "LIMIT":
                    globalVar['profit_count'] += 1
                msg = '\n'.join(
                    ['盈利次数: ' + str(globalVar['profit_count']) + ' 次',
                     '亏损次数: ' + str(globalVar['loss_count']) + ' 次',
                     '总运行时长: ' + str(round((time.time() - init_time) / 3600, 2)) + ' 小时',
                     '总盈亏: ' + str(globalVar['balance'] - globalVar['init_balance']) + ' U',
                     '本次开仓时长: ' + str(round((time.time() - globalVar['this_time']) / 3600, 2)) + ' 小时',
                     '本单盈亏: ' + str(message['o']['rp']) + ' U'])
                globalVar['this_time'] = time.time()
                print(msg)
                notifyService = NotifyService(msg)
                notifyService.sendMessageToWeiXin()
                globalVar['piece'] += 1

        thread.start_new_thread(run, ())
    elif message['e'] == "ACCOUNT_UPDATE":
        globalVar['balance'] = float(message['a']['B'][0]['wb'])


def long(symbol, quantity, take_profit_scope, stop_scope):
    msg = '做多 ' + symbol + ' 量：' + quantity
    print(msg)
    notifyService = NotifyService(msg)
    notifyService.sendMessageToWeiXin()
    longOrderId = order(symbol, 'BUY', 'LONG', 'MARKET', quantity, '')['orderId']
    price = getOrderPrice(symbol, longOrderId)
    # 止损
    stop_price = str(round(float(price) * (1 - stop_scope), 2))
    res = order(symbol, 'SELL', 'LONG', 'STOP_MARKET', quantity, '', stop_price)
    stop_orderId = res['orderId']
    status = res['status']
    if status == 'NEW':
        # 止盈
        take_profit_price = str(round(float(price) * (1 + take_profit_scope), 2))
        take_profit_orderId = order(symbol, 'SELL', 'LONG', 'LIMIT', quantity, take_profit_price)['orderId']
        globalVar['orderMap'][take_profit_orderId] = stop_orderId
        globalVar['orderMap'][stop_orderId] = take_profit_orderId


def short(symbol, quantity, take_profit_scope, stop_scope):
    msg = '做空 ' + symbol + ' 量：' + quantity
    print(msg)
    notifyService = NotifyService(msg)
    notifyService.sendMessageToWeiXin()
    shortOrderId = order(symbol, 'SELL', 'SHORT', 'MARKET', quantity, '')['orderId']
    price = getOrderPrice(symbol, shortOrderId)
    # 止损
    stop_price = str(round(float(price) * (1 + stop_scope), 2))
    res = order(symbol, 'BUY', 'SHORT', 'STOP_MARKET', quantity, '', stop_price)
    stop_orderId = res['orderId']
    status = res['status']
    if status == 'NEW':
        # 止盈
        take_profit_price = str(round(float(price) * (1 - take_profit_scope), 2))
        take_profit_orderId = order(symbol, 'BUY', 'SHORT', 'LIMIT', quantity, take_profit_price)['orderId']
        globalVar['orderMap'][take_profit_orderId] = stop_orderId
        globalVar['orderMap'][stop_orderId] = take_profit_orderId


def loop():
    def run():
        while True:
            time.sleep(random.random() * 5 * 60)
            if globalVar['piece'] > 0:
                data = getKline(symbol, interval)
                res = macdjincha(data)
                if res == 'up':
                    long(symbol, quantity, take_profit_scope, stop_scope)
                    globalVar['piece'] -= 1
                elif res == 'down':
                    short(symbol, quantity, take_profit_scope, stop_scope)
                    globalVar['piece'] -= 1

    thread.start_new_thread(run, ())
