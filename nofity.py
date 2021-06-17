import json
import requests


class NotifyService(object):
    def __init__(self, message):
        self.message = message

    def sendMessageToWeiXin(self):
        data = {
            "appToken": "AT_U950xOUDtPQmzFNzOLwI99TaDGPvS7rp",
            "content": self.message,
            "contentType": 1,  # 内容类型 1表示文字  2表示html(只发送body标签内部的数据即可，不包括body标签) 3表示markdown
            "topicIds": [  # 发送目标的topicId，是一个数组！！！
                123
            ],
            "uids": [  # 发送目标的UID，是一个数组！！！
                "UID_Hoe5dkX9dnPXf9QyYj51cTGu3suh",
                "UID_QcQLiLQZSxxjKPbM80wTqXOMJkJP",
                'UID_S69EAHJVgFPxpUqgzCpGaUHZBnwj',  # 范天伟
                # "UID_Lzi5IAljUc45Rq27M6zNKdAb9unm",  # 刘春桃
                # "UID_3FScq4H1FgG92RaoRT5Fx5VrnV5p",
                # "UID_lSXk2aqmLsHaQoWxTyosPyVegBTZ",
                # "UID_ceA46CD7UBTr1oRqGN7Gd9evieur"
            ]
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post('http://wxpusher.zjiecode.com/api/send/message', data=json.dumps(data), headers=headers)