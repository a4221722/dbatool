#!/usr/bin/env python
# -*- coding=utf-8 -*-
__author__='luoji'

import logging

from settings import log_level,logname
def dtLog(message,level,logname=logname,loglevel=log_level):
    logger = logging.getLogger('dbalogger')
    logger.setLevel(getattr(logging,loglevel.upper()))
    fh = logging.FileHandler(logname)
    formatter = logging.Formatter('%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    fh.setLevel(getattr(logging,loglevel.upper()))
    logger.addHandler(fh)
    func=getattr(logger,level.lower())
    func(message)
    logger.removeHandler(fh)
