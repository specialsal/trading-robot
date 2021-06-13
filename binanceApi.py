import hashlib
import hmac
import requests
from config import *


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