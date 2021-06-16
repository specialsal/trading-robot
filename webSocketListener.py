import hmac
import hashlib
import websocket
import requests
from config import *
from strategy1 import dealMsg


def on_message(ws, message):
    message = json.loads(message)
    print(message)
    if message['e'] == "listenKeyExpired":
        print('listenKey过期')
        ws.close()
        listen()
    else:
        dealMsg(message)


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