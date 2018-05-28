#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'

def color(msg,color):
    if color == 'r':
        return '\033[1;35m '+msg+' \033[0m'
    elif color == 'g':
        return '\033[1;32m '+msg+' \033[0m'
    elif color == 'y':
        return '\033[1;33m '+msg+' \033[0m'

