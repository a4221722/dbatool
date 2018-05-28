#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'

class BasicDb():
    def __init__(self,*arg):
        print('not supported now')
        return

    def checkConnect(self):
        return False

    def exec(self,statement):
        print('not supported now')

    def getTabStr(self,schema,tab):
        return '',''

    def getIndStr(self,schema,tab):
        return '',''

    def commit(self):
        print('not supported now')

    def rollback(self):
        print('not supported now')

