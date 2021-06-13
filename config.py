import json


file = open('./config.json', 'r')
config = json.loads(file.read())
host = config['host']
api_key = config['api_key']
secret_key = config['secret_key']
headers = config['headers']