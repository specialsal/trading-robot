#!/usr/bin/env python3
# coding=utf-8
# from strategy1 import *
import random
from strategy2 import *
from webSocketListener import listen
from util import *


globalVar['init_balance'] = getBalance()  # 初始资产


def main():
    loop()
    listen()


main()