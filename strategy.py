#!/usr/bin/env python3
# coding=utf-8
import random
from notify import NotifyService
from binanceApi import *
from webSocketListener import listen

try:
    import thread
except ImportError:
    import _thread as thread


def hold(symbol, _type):
    level(symbol, leverage)
    allQuantity = str(float(quantity) * piece)
    if _type == 'LONG':
        print('做多 ' + symbol + ' 量：' + allQuantity)
        longOrderId = order(symbol, 'BUY', 'LONG', 'MARKET', allQuantity, '')['orderId']
        price = getOrderPrice(symbol, longOrderId)
        # 止盈
        take_profit_price = str(round(float(price) * (1 + 0.1), 2))
        res = order(symbol, 'SELL', 'LONG', 'TRAILING_STOP_MARKET', allQuantity, take_profit_price, '', '', '5')
        take_profit_orderId = res['orderId']
        status = res['status']
        if status == 'NEW':
            # 止损
            stop_price = str(round(float(price) * (1 - stop_scope), 2))
            res = order(symbol, 'SELL', 'LONG', 'STOP_MARKET', quantity, '', stop_price)
            stop_orderId = res['orderId']
            globalVar['orderMap'][take_profit_orderId] = stop_orderId
            globalVar['orderMap'][stop_orderId] = take_profit_orderId
    elif _type == 'SHORT':
        print('做空 ' + symbol + ' 量：' + allQuantity)
        shortOrderId = order(symbol, 'SELL', 'SHORT', 'MARKET', allQuantity, '')['orderId']
        price = getOrderPrice(symbol, shortOrderId)
        # 止盈
        take_profit_price = str(round(float(price) * (1 - 0.1), 2))
        res = order(symbol, 'BUY', 'SHORT', 'TRAILING_STOP_MARKET', allQuantity, '', '', take_profit_price, '5')
        take_profit_orderId = res['orderId']
        status = res['status']
        if status == 'NEW':
            # 止损
            stop_price = str(round(float(price) * (1 + stop_scope), 2))
            res = order(symbol, 'BUY', 'SHORT', 'STOP_MARKET', quantity, '', stop_price)
            stop_orderId = res['orderId']
            globalVar['orderMap'][take_profit_orderId] = stop_orderId
            globalVar['orderMap'][stop_orderId] = take_profit_orderId


def bounce(symbol):
    level(symbol, leverage)
    # 随机选择一个多空方向
    if random.random() < globalVar['pivot']:
        print('做多 ' + symbol + ' 量：' + quantity)
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
    else:
        print('做空 ' + symbol + ' 量：' + quantity)
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


def dealMsg(ws, message):
    if message['e'] == "listenKeyExpired":
        print('listenKey过期')
        ws.close()
        listen()
    elif message['e'] == "ORDER_TRADE_UPDATE" and message['o']['x'] == "TRADE" and message['o']['X'] == "FILLED" and \
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
                _type = ''
                if message['o']['ot'] == "STOP_MARKET":
                    globalVar['loss_count'] += 1
                    if message['o']['S'] == 'SELL':
                        globalVar['pivot'] -= stop_market_energy_ratio
                    elif message['o']['S'] == 'BUY':
                        globalVar['pivot'] += stop_market_energy_ratio
                elif message['o']['ot'] == "LIMIT":
                    globalVar['profit_count'] += 1
                    if message['o']['S'] == 'SELL':
                        globalVar['pivot'] += take_profit_energy_ratio
                    elif message['o']['S'] == 'BUY':
                        globalVar['pivot'] -= take_profit_energy_ratio
                # 设置开仓概率最大限度
                if globalVar['pivot'] > 1:
                    globalVar['pivot'] = 1
                elif globalVar['pivot'] < 0:
                    globalVar['pivot'] = 0
                msg = '\n'.join(
                    ['盈利次数: ' + str(globalVar['profit_count']) + ' 次',
                     '亏损次数: ' + str(globalVar['loss_count']) + ' 次',
                     '目前开多概率: ' + str(globalVar['pivot']),
                     '总运行时长: ' + str(round((time.time() - init_time) / 3600, 2)) + ' 小时',
                     '总盈亏: ' + str(globalVar['balance'] - init_balance) + ' U',
                     '本次开仓时长: ' + str(round((time.time() - globalVar['this_time']) / 3600, 2)) + ' 小时',
                     '本单盈亏: ' + str(message['o']['rp']) + ' U'])
                globalVar['this_time'] = time.time()
                print(msg)
                notifyService = NotifyService(msg)
                notifyService.sendMessageToWeiXin()
                time.sleep(random.random() * 15 * 60)
                bounce(symbol)

        thread.start_new_thread(run, ())
    elif message['e'] == "ACCOUNT_UPDATE":
        globalVar['balance'] = float(message['a']['B'][0]['wb'])


def main():
    def run():
        for i in range(piece):
            bounce(symbol)
            time.sleep(random.random()*15*60)

    thread.start_new_thread(run, ())
    listen()


symbol = 'ETHUSDT'  # 交易对
quantity = '0.01'  # 交易量
piece = 10
leverage = '1'  # 合约倍数
take_profit_scope = 0.0125  # 止盈幅度
stop_scope = 0.04  # 止损幅度
init_time = time.time()  # 开机时间
init_balance = getBalance()  # 初始资产
# 盈利次数，亏损次数，当前时间，当前资产，止盈止损订单对
globalVar = {'profit_count': 0, 'loss_count': 0, 'this_time': init_time, 'balance': 0, 'pivot': 0.5, 'orderMap': {}}
take_profit_energy_ratio = 0.05
stop_market_energy_ratio = 0.2
main()
