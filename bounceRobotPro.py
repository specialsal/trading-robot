#!/usr/bin/env python3
# coding=utf-8
import hashlib
import hmac
import json
import requests
import websocket
import time
import random
from nofity import NotifyService

try:
    import thread
except ImportError:
    import _thread as thread

# 币安
file = open('./config.json', 'r')
config = json.loads(file.read())
host = config['host']
api_key = config['api_key']
secret_key = config['secret_key']
headers = config['headers']


def getTime():
    return str(int(time.time() * 1000))


def getBalance():
    method = '/fapi/v2/balance'
    timestamp = str(getTime())
    msg = '&'.join(
        ['timestamp=' + timestamp])
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.get(
        'https://' + host + method + '?timestamp=' + timestamp + '&signature=' + signature,
        headers=headers)
    content = json.loads(response.content)
    print('资产: ', str(content[1]['balance']), ' U')
    return float(content[1]['balance'])


def getUserData(symbol):
    method = '/fapi/v2/account'
    timestamp = str(getTime())
    msg = '&'.join(
        ['timestamp=' + timestamp])
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.get(
        'https://' + host + method + '?timestamp=' + timestamp + '&signature=' + signature,
        headers=headers)
    content = json.loads(response.content)
    long = ''
    short = ''
    for i in range(len(content['positions'])):
        if content['positions'][i]['symbol'] == symbol:
            if content['positions'][i]['positionSide'] == 'LONG':
                long = content['positions'][i]['positionAmt']
            if content['positions'][i]['positionSide'] == 'SHORT':
                short = content['positions'][i]['positionAmt']
    print('资产: ', str(content['positions']), ' U')
    return {'long': float(long), 'short': -float(short)}


def getPrice(symbol):
    method = '/fapi/v1/ticker/price'
    timestamp = str(getTime())
    params = ['symbol=' + symbol,
              'timestamp=' + timestamp]
    msg = '&'.join(params)
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.get('https://' + host + method + '?' + msg + '&signature=' + signature,
                            headers=headers)
    content = json.loads(response.content)
    print(content)
    return content['price']


def level(symbol, leverage='1'):
    # 币安
    method = '/fapi/v1/leverage'
    timestamp = str(getTime())
    msg = '&'.join(
        ['symbol=' + symbol, 'leverage=' + leverage, 'timestamp=' + timestamp])
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.post(
        'https://' + host + method + '?symbol=' + symbol + '&leverage=' + leverage + '&timestamp=' + timestamp + '&signature=' + signature,
        headers=headers)
    content = json.loads(response.content)
    print('设置合约倍数为：' + leverage)
    return content


def getOrderPrice(symbol, orderId):
    # 获取已成交订单的成交价格
    method = '/fapi/v1/order'
    orderId = str(orderId)
    timestamp = str(getTime())
    msg = '&'.join(
        ['symbol=' + symbol, 'orderId=' + orderId,
         'timestamp=' + timestamp])
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.get(
        'https://' + host + method + '?symbol=' + symbol + '&orderId=' + orderId +
        '&timestamp=' + timestamp + '&signature=' + signature,
        headers=headers)
    content = json.loads(response.content)
    if 'avgPrice' in content:
        price = str(round(float(content['avgPrice']), 2))
        print('成交价: ' + price)
        return price
    return '0.0'


def order(symbol, side, positionSide, type, quantity, price, stopPrice='', activationPrice='', callbackRate='5',
          closePosition='false'):
    print('下单')
    print('stopPrice ', stopPrice)
    method = '/fapi/v1/order'
    timestamp = str(getTime())
    params = ['symbol=' + symbol, 'side=' + side, 'type=' + type,
              'positionSide=' + positionSide,
              'timestamp=' + timestamp, 'quantity=' + quantity]
    if closePosition == 'true':
        params.pop()
        params.append('closePosition=' + str(closePosition))
    if type == 'LIMIT':
        price = str(round(float(price), 2))
        params.append('price=' + price)
        params.append('timeInForce=' + 'GTC')
    if type == 'STOP_MARKET':
        if stopPrice == '':
            stopPrice = '0'
        stopPrice = str(round(float(stopPrice), 2))
        params.append('stopPrice=' + stopPrice)
    if type == 'TRAILING_STOP_MARKET':
        params.append('activationPrice=' + str(activationPrice))
        params.append('callbackRate=' + str(callbackRate))

    msg = '&'.join(params)
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.post('https://' + host + method + '?' + msg + '&signature=' + signature,
                             headers=headers)
    content = json.loads(response.content)
    print('挂单成功 ', 'price ', price, 'stopPrice ', stopPrice)
    print(content)
    if 'orderId' in content:
        return {'orderId': content['orderId'], 'status': content['status']}
    return {'orderId': 0, 'status': 'FAILED'}


def deleteAllOrder(symbol):
    method = '/fapi/v1/allOpenOrders'
    timestamp = str(getTime())
    msg = '&'.join(
        ['symbol=' + symbol,
         'timestamp=' + timestamp])
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.delete(
        'https://' + host + method + '?symbol=' + symbol +
        '&timestamp=' + timestamp + '&signature=' + signature,
        headers=headers)
    content = json.loads(response.content)
    print('删除所有挂单')
    print(content)


def deleteAllPosition(symbol):
    price = getPrice(symbol)
    res = getUserData(symbol)
    longQuantity = res['long']
    shortQuantity = res['short']
    if longQuantity > 0:
        order(symbol, 'SELL', 'LONG', 'MARKET', str(longQuantity), '', str(round(float(price) * 1.2, 2)))
    if shortQuantity > 0:
        order(symbol, 'BUY', 'SHORT', 'MARKET', str(shortQuantity), '', str(round(float(price) * 0.8, 2)))


def deleteOrder(symbol, orderId):
    method = '/fapi/v1/order'
    orderId = str(orderId)
    timestamp = str(getTime())
    msg = '&'.join(
        ['symbol=' + symbol,
         'timestamp=' + timestamp, 'orderId=' + orderId])
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.delete(
        'https://' + host + method + '?' + msg + '&signature=' + signature,
        headers=headers)
    content = json.loads(response.content)
    print('取消挂单: ', orderId)
    print(content)


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


def on_message(ws, message):
    message = json.loads(message)
    print(message)
    dealMsg(ws, message)


def on_error(ws, error):
    print(ws)
    print(error)


def on_close(ws):
    print("### 关闭WebSocket ###")
    listen()


def on_open(ws):
    pass


def getListenKey():
    method = '/fapi/v1/listenKey'
    signature = hmac.new(bytes(secret_key, 'utf-8'), msg=bytes('', 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    response = requests.post(
        'https://' + host + method + '?signature=' + signature,
        headers=headers)
    content = json.loads(response.content)
    print('获取listenKey')
    return content['listenKey']


def listen():
    listenKey = getListenKey()
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + listenKey,
                                on_message=on_message,
                                on_error=on_error,
                                on_open=on_open,
                                on_close=on_close)
    print('重启WebSocket')
    ws.run_forever(sslopt={"check_hostname": False})


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
