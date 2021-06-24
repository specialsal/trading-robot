import json
import time

# 交易所API配置
file = open('./config.json', 'r')
config = json.loads(file.read())
host = config['host']
secret_key = config['secret_key']
headers = config['headers']

# 交易信息配置
symbol = 'ETHUSDT'  # 交易对
quantity = '0.01'  # 交易量
piece = 10
leverage = '1'  # 合约倍数
take_profit_scope = 0.0125  # 止盈幅度
stop_scope = 0.05  # 止损幅度
init_time = time.time()  # 开机时间
interval = '15m'  # 15分钟k线
# 盈利次数，亏损次数，当前时间，当前资产，止盈止损订单对
globalVar = {'init_balance': 0, 'profit_count': 0, 'loss_count': 0, 'this_time': init_time, 'balance': 0, 'pivot': 0.5,
             'orderMap': {}, 'piece': 1}
take_profit_energy_ratio = 0.05
stop_market_energy_ratio = 0.2
