#!/usr/bin/env python
# -*- coding=utf-8 -*-

__author__='luoji'
import os

baseDir = os.path.dirname(os.path.abspath(__file__))
#sqllite库路径
dbPath = baseDir+'/db/dba.db'

#日志级别
log_level='debug'

#日志路径
logname=baseDir+'/log/dbatool.log'

#数据库类型和对应的表名映射关系
tabMap = {
    'oracle':'oracle_instances',
    'mysql':'mysql_instances',
}

#表名和列名的映射关系，要和sqlite中的表结构一致
colMap = {
    'oracle_instances':['id','name','host','port','sid','username','password','charset'],
    'mysql_instances':['id','name','host','port','username','password','charset'],
}

#建立数据库连接需要的字段,并集
connectList = ['name','host','port','sid','username','password','charset']

#可选的数据库类型
dbChoices = ['oracle','mysql']

