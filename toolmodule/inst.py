#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'
from toolmodule.args import args
from settings import dbPath,tabMap,colMap
import sqlite3
from utils.aes_decryptor import Prpcrypt

prpcrypt=Prpcrypt()
#类名就是一级命令，函数名是二级命令
class Inst():
    def __init__(self):
        self._dbConnect = sqlite3.connect(dbPath)
        self._dbCursor = self._dbConnect.cursor()

    #添加args,默认显示oracle的实例信息
    @args('-t',dest='typ',action='store',
         choices={'oracle','mysql'},default='oracle',
         help='instance typ')
    #展示实例信息
    def show(self,**kwargs):
        typ=kwargs['typ']
        colList = [col for col in colMap[tabMap[typ]] if col.lower() not in ('password')]
        selectSql='select "'+'","'.join(str(col) for col in colList)+'" from '+tabMap[typ]
        self._dbCursor.execute(selectSql)
        print('|'.join(format(header[0],'>10')for header in self._dbCursor.description))
        for colList in self._dbCursor:
            print('|'.join([format(val,'>10') for val in colList]))

    #添加args
    @args('-t',dest='typ',action='store',
         choices={'oracle','mysql'},default='oracle',
         help='instance typ')
    @args('-n',dest='name',action='store',required=True,
         help='instance typ')
    @args('-H',dest='host',required=True,action='store',
         help='host name or ip')
    @args('-p',dest='port',action='store',default=1521,
         help='instance port')
    @args('-s',dest='sid',action='store',
         help='service name')
    @args('-u',dest='username',required=True,action='store',
         help='database user name')
    @args('-P',dest='password',required=True,action='store',
         help='database password')
    @args('-c',dest='charset',required=True,action='store',
         choices={'gbk','utf-8'},help='database client charset')
    @args('-g',dest='group',action='store',
         help='instance group')
    #增加实例信息
    def add(self,**kwargs):
        typ=kwargs['typ']
        if typ == 'oracle' and not kwargs['sid']:
            print('Should provide service name for Oracle instance')
            return
        try:
            colList = [col for col in colMap[tabMap[typ]] if col.lower() not in ('id')]
            insertSql = 'insert into '+tabMap[typ]+'("'+'","'.join(colList)+'") values('+ len(colList)*'?,'
            insertSql = insertSql.rstrip(',')+')'
            kwargs['password'] = prpcrypt.encrypt(kwargs['password'])
            arg=[ val for key,val in kwargs.items() if key in colList]
            self._dbCursor.execute(insertSql,arg)
        except Exception as err:
            print(str(err))
        else:
            self._dbConnect.commit()

    @args('-t',dest='typ',action='store',
         choices={'oracle','mysql'},default='oracle',
         help='instance typ')
    @args('-d',dest='id',action='store')
    #根据类型和id删除实例信息
    def delete(self,**kwargs):
        typ=kwargs['typ']
        try:
            deleteSql = 'delete from '+tabMap[typ]+' where id = '+kwargs['id']
            self._dbCursor.execute(deleteSql)
        except Exception as err:
            print(str(err))
        else:
            self._dbConnect.commit()
            print('delete instance successfully')


