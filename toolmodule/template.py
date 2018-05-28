#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'
from toolmodule.args import args

class Template():
    def __init__(self):
        pass

    @args('-t',dest='type',required=True, action='store',
         choices={'oracle','mysql'},default='oracle',
         help='instance type')
    def add(self,type):
        print(('going to add {} instance').format(type))

