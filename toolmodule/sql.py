#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'
from prompt_toolkit import prompt
from prompt_toolkit.token import Token
from prompt_toolkit.history import InMemoryHistory,FileHistory
from toolmodule.args import args
import sqlite3
from settings import *
from toolmodule.oradb import Oradb
from toolmodule.mydb import Mydb
from pygments.lexers.sql import PostgresLexer
import re
from toolmodule.logger import Logger
#import codecs
import os
from math import ceil
from os import get_terminal_size
import datetime

objMap = {
    'oracle':Oradb,
    'mysql':Mydb
}

def get_continuation_tokens(cli, width):
        return [(Token, '.' * width)]

dmlPattern = re.compile(r'^\s*(/\*.*\*/)?\s*(alter|comment|grant|create|update|insert|drop|delete).+$',re.DOTALL)
selPattern = re.compile(r'^\s*((--.*\n+)|(/\*.*\*/))*\s*(select).+$',re.DOTALL)

#astarBgPatter = re.compile(r'^\s*/\*.*$',re.DOTALL)
#astarEdPatter = re.compile(r'^\s*\*/.*$',re.DOTALL)


class Sql():
    #初始化sqlite连接和游标
    def __init__(self):
        self._dbConnect = sqlite3.connect(dbPath)
        self._dbCursor = self._dbConnect.cursor()
        #self.history=FileHistory('./history/sql.his')
        self.history=InMemoryHistory()
        self.cmdLogger=Logger(logname=logname,filename=__file__)

    def _maniFile(self,inFile,charset):
        try:
            with open(inFile,'r') as f:
                lines=f.readlines()
                sqlContent=''
                for line in lines:
                    sqlContent+=self._lineFilter(line)
            sqlList = sqlContent.rstrip('\n').rstrip(';').split(';')
            lastSql = ''
            for i in range(0,len(sqlList)):
                sql = lastSql+sqlList[i]
                cntSemi = sql.count("'")
                if cntSemi % 2 != 0:
                    lastSql = sql+';'
                    continue
                else:
                    lastSql = ''
                if dmlPattern.match(sql.lower()):
                    yield sql
                else:
                    print('Error: unsupported operation: '+sql)
                    #if sql.rstrip('\n').strip().endswith(';'):
                    #    sql=sql.rstrip('\n').strip().rstrip(';')
                    #    if dmlPattern.match(sql.lower()):
                    #        yield sql.rstrip(';\n')
                    #    else:
                    #        print('Error: unsupported operation: '+sql)
                    #    sql=''
        except Exception as err:
            self.cmdLogger.write(str(err),'error')
            print('check file previledges or contents')

    def _lineFilter(self,line):
        linePatter = re.compile(r'^\s*-{2,}.*$')
        if linePatter.match(line):
            return ''
        else:
            return line

    @args('-t',dest='typ',required=True, action='store',
         choices=dbChoices,default='oracle',
         help='instance type')
    @args('-d',dest='id',action='store',nargs='*',
         help='ids of instances to be connected')
    @args('-n',dest='name',action='store',nargs='*',
         help='names of instances to be connected')

    def exe(self,**kwargs):

        #判断连接的数据库类型，后面对应到不同的sqlite表
        typ=kwargs['typ']

        #id或者name至少输入一个
        if not kwargs['id'] and not kwargs['name']:
            print("'-d' or '-n' must be assigned!")
            return

        #根据输入的id拼接where条件，从sqlite里拿出数据库连接信息
        if (kwargs['id'] and kwargs['id'][0] == 'all') or (kwargs['name'] and kwargs['name'][0] == 'all'):
            whereSt=' where 1=1 '
        else:
            whereSt=' where 1=2 '
            whereId=''
            whereNm=''
            if kwargs['id']:
                whereId = ' or id in ('
                for id in kwargs['id']:
                    if id.isdigit():
                        whereId += str(id)+','
                    else:
                        print('id must be integer!')
                        return
                whereId = whereId.rstrip(',')+')'
            if kwargs['name']:
                whereNm = ' or name in('
                for name in kwargs['name']:
                    whereNm += "'"+name+"',"
                whereNm = whereNm.rstrip(',')+')'
            whereSt = whereSt + whereId + whereNm

        colList = [col for col in colMap[tabMap[typ]] if col.lower() in connectList]
        selectSql='select '+','.join(str(col) for col in colList)+' from '+tabMap[typ]+whereSt
        self._dbCursor.execute(selectSql)
        result=self._dbCursor.fetchall()
        if not result:
            print('Instances does not exist!')
            return

        #使用取到的数据库连接信息，分别创建对应的数据对象，连接正常的放到列表里
        dbObjList = []
        for colList in result:
            dbObj = objMap[typ](*colList)
            connectSt=dbObj.checkConnect()
            if connectSt:
                dbObjList.append(dbObj)
            else:
                continue
        print(str(len(dbObjList))+' instances connected.')
        text = prompt("Go on Y/N? ")
        while True:
            text = text.strip().upper()
            if text == 'Y':
                break
            elif text == 'N':
                return
            else:
                print("please enter Y or N")

        #进入sql界面
        print("Enter your statement ending with ';'. Press 'Esc'+'Enter' to complete the input.")
        report=0
        record=0
        rf=None
        while True:
            #是否开启报表功能
            try:
                text = prompt("SQL> ",multiline=True,lexer=PostgresLexer,get_continuation_tokens=get_continuation_tokens,history=self.history)
                text=text.strip()
                if not text:
                    continue
                elif text.endswith(';'):
                    if rf:
                        rf.write('\n'+'#'*ceil(get_terminal_size().columns*0.5)+'\n'+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n'+text)
                    text = text.rstrip(';').strip()
                    if text.lower() in ('exit','quit'):
                        break
                    elif text.lower() in ('commit','rollback'):
                        for dbObj in dbObjList:
                            func = getattr(dbObj,text)
                            func(rf)
                    elif re.match(r'^spool(\s+)on$',text.lower()):
                        report=1
                        if not os.path.exists('./report'):
                            try:
                                os.system('mkdir report')
                            except Exception as err:
                                print('Can not create report directory.')
                            else:
                                pass
                    elif re.match(r'^record(\s+)on(.*)$',text.lower()):
                        record = 1
                        mt = re.match(r'^record(\s+)on(.*)$',text.lower())
                        if mt.group(2):
                            recordFile = mt.group(2).lstrip()
                        else:
                            recordFile = './log/'+'_'.join(['sql',datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")])
                        rf = open(recordFile,'a')
                    elif re.match(r'^spool\s+off$',text.lower()):
                        report=0
                    elif re.match(r'^record\s+off$',text.lower()):
                        if rf:
                            rf.close()
                            rf=None
                    elif dmlPattern.match(text.lower()):
                        text=text.rstrip(';')
                        for dbObj in dbObjList:
                            dbObj.exec(text,rf)
                    elif selPattern.match(text.lower()):
                        for dbObj in dbObjList:
                            dbObj.sel(text,report)
                    else:
                        print('Invalid Sql')
                        continue
                    if rf:
                        rf.write('\n'+'#'*ceil(get_terminal_size().columns*0.5)+'\n'+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n'+text)
                elif text.lower() in ('exit','quit'):
                    break
                elif text.startswith('@'):
                    inFileList = text.lstrip('@').split(',')
                    for dbObj in dbObjList:
                        for inFile in inFileList:
                            for sql in self._maniFile(inFile,dbObj.charset):
                                if rf:
                                    rf.write('\n'+'#'*ceil(get_terminal_size().columns*0.5)+'\n'+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                    rf.write('\n'+sql)
                                try:
                                    dbObj.exec(sql,rf)
                                except Exception as err:
                                    print(str(err))
                                finally:
                                    if rf:
                                        rf.write('\n'+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n'+'#'*ceil(get_terminal_size().columns*0.5))
                else:
                    print("Sql must end with ';'")
            except EOFError:
                break
            except KeyboardInterrupt:
                print('Operation cancelled.')
                continue
            except Exception as err:
                cmdLogger.write(str(err),'error')
                print(str(err))
                return

