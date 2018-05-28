#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'
import argparse
from toolmodule.inst import Inst
from toolmodule.sql import Sql
from toolmodule.check import Check

#一级命令对应的类
#如果要添加一级命令，在cmdTree里添加一组k:v，并创建相应的模块导
cmdTree = {
    'inst':Inst,
    'sql':Sql,
    'check':Check,
}

def methods_of(obj):
    result = []
    for i in dir(obj):
        if callable(getattr(obj,i)) and not i.startswith('_'):
            result.append((i,getattr(obj,i)))
    return result

def gn_parser():
    parser = {}
    for k in cmdTree.keys():
        parser[k] = argparse.ArgumentParser(prog=k)
        command_object = cmdTree[k]()
        parser[k].set_defaults(command_object=command_object)
        subparsers=parser[k].add_subparsers()

        for action,action_fn in methods_of(command_object):
            subParser = subparsers.add_parser(action)

            action_kwargs = []
            for args,kwargs in getattr(action_fn, 'args', []):
                subParser.add_argument(*args, **kwargs)

            subParser.set_defaults(action_fn=action_fn)
            subParser.set_defaults(action_kwargs=action_kwargs)
    return parser

