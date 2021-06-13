#!/usr/bin/env python3
# coding=utf-8
from strategy import *
from webSocketListener import listen


def main():
    def run():
        for i in range(piece):
            bounce(symbol)
            time.sleep(random.random()*15*60)

    thread.start_new_thread(run, ())
    listen()


main()