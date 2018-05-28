#!/usr/bin/env python
# -*- coding=utf-8 -*-
__author__='luoji'

import logging

from settings import log_level
class Logger():
    def __init__(self,logname,filename,loglevel=log_level):
        self.logger = logging.getLogger('dbalogger')
        self.logger.setLevel(getattr(logging,loglevel.upper()))
        self.fh = logging.FileHandler(logname)
        formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
        self.fh.setFormatter(formatter)
        self.fh.setLevel(getattr(logging,loglevel.upper()))
        if  loglevel.lower() == 'debug':
            self.filename=filename
        else:
            self.filename=''

    def write(self,message,level):
        self.logger.addHandler(self.fh)
        func=getattr(self.logger,level.lower())
        func(self.filename+'-'+message)
        self.logger.removeHandler(self.fh)
    
    def __exit__(self):
        self.logger.removeHandler(self.fh)
