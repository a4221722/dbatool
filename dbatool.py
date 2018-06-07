#! /usr/bin/env python
# -*- coding=utf-8 -*-
__authot__='luoji'
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory,FileHistory
from toolmodule.parser import gn_parser,cmdTree
from toolmodule.logger import Logger
from settings import logname
import argparse
import sys

cmdTitle = "Welcome to Dba SQL Tool. Type help for available commands."
promptTitle = "DBA>> "


def fetch_func_args(func,matchargs):
    fn_kwargs = {}
    for args,kwargs in getattr(func,'args',[]):
        arg = kwargs['dest']
        fn_kwargs[arg]=(getattr(matchargs,arg))

    return fn_kwargs

if __name__ == '__main__':
    
    parser = gn_parser()
    cmdLogger=Logger(logname=logname,filename=__file__)
    #history=FileHistory('./history/cmd.his')
    history=InMemoryHistory()
    print(cmdTitle)
    while True:
        try:
            text = prompt(promptTitle,history=history)
            text = text.strip()
            if text.lower() in ('exit','quit'):
                break
            elif not text:
                continue
            elif text.lower() in ('help','h'):
                print('Valid operations: ')
                for k in cmdTree.keys():
                    print(' '*4+k)
                continue
            else:
                textList = text.split()
                if textList[0] in cmdTree.keys() and len(textList) == 1:
                    textList.append('-h')
            match_args = parser[textList[0]].parse_args(textList[1:])
            fn = match_args.action_fn
            fn_kwargs = fetch_func_args(fn,match_args)
            fn(**fn_kwargs)
        except SystemExit:
            continue
        except EOFError:
            break
        except KeyboardInterrupt:
            print('Operation cancelled.')
            continue
        except Exception as err:
            cmdLogger.write(str(err),'error')
            print('Invalid operatioin.')
