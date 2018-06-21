#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory,FileHistory
from prompt_toolkit.key_binding import KeyBindings
from toolmodule.args import args
import sqlite3
from settings import *
from dao.oradb import Oradb
from dao.mydb import Mydb
from pygments.lexers.sql import PostgresLexer
import re
from utils.logger import Logger
#import codecs
import os
import pdb
from math import ceil
from os import get_terminal_size
import datetime
from threading import Thread
from prompt_toolkit import PromptSession
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
objMap = {
    'oracle':Oradb,
    'mysql':Mydb
}

def prompt_continuation(width, line_number, is_soft_wrap):
        return  '.' * width


bindings = KeyBindings()
@bindings.add('c-m')
def eof(event):
    if event.cli.current_buffer.text.rstrip().endswith(';'):
        event.current_buffer.validate_and_handle()
    else:
        event.cli.current_buffer.insert_text('\n')

class workThread(Thread):
    def __init__(self,func,args=()):
        super(workThread,self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

dmlPattern = re.compile(r'^\s*(/\*.*\*/)?\s*(alter|comment|grant|create|update|insert|drop|delete|truncate|revoke).+$',re.DOTALL)
selPattern = re.compile(r'^\s*((--.*\n+)|(/\*.*\*/))*\s*(select).+$',re.DOTALL)
procPattern = re.compile(r'^\s*exec\s+(\w+\.?\S+)\s*$')

#astarBgPatter = re.compile(r'^\s*/\*.*$',re.DOTALL)
#astarEdPatter = re.compile(r'^\s*\*/.*$',re.DOTALL)


class Sql():
    #初始化sqlite连接和游标
    def __init__(self):
        self._dbConnect = sqlite3.connect(dbPath)
        self._dbCursor = self._dbConnect.cursor()
        #self.cmdHistory=FileHistory('./history/sql.his')
        self.cmdHistory=InMemoryHistory()
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
    @args('-d',dest='id',action='store',
         help='ids of instances to be connected')
    @args('-n',dest='name',action='store',
         help='names of instances to be connected')
    @args('-g',dest='group',action='store',
         help='groups of instances to be connected')

    def exe(self,**kwargs):

        #判断连接的数据库类型，后面对应到不同的sqlite表
        typ=kwargs['typ']

        #id或者name至少输入一个
        if not kwargs['id'] and not kwargs['name'] and not kwargs['group']:
            print("'-d', '-n'  or '-g' must be assigned!")
            return

        #根据输入的id拼接where条件，从sqlite里拿出数据库连接信息
        if (kwargs['id'] and kwargs['id'] == 'all') or (kwargs['name'] and kwargs['name'] == 'all'):
            whereSt=' where 1=1 '
        else:
            whereSt=' where 1=2 '
            whereId=''
            whereNm=''
            whereGp=''
            if kwargs['id']:
                whereId = ' or id in ('
                for id in kwargs['id'].split(','):
                    if id.isdigit():
                        whereId += str(id)+','
                    else:
                        print('id must be integer!')
                        return
                whereId = whereId.rstrip(',')+')'
            if kwargs['name']:
                whereNm = ' or name in('
                for name in kwargs['name'].split(','):
                    whereNm += "'"+name+"',"
                whereNm = whereNm.rstrip(',')+')'
            if kwargs['group']:
                groups = kwargs['group'].split(',')
                whereGp = """ or "group" in ('"""+"','".join(groups)+"')"
            whereSt = whereSt + whereId + whereNm + whereGp

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
        print("Enter your statement ending with ';'. ")
        report=0
        record=0
        rf=None
        sqlSession = PromptSession(history = self.cmdHistory)
        while True:
            #是否开启报表功能
            try:
                text = sqlSession.prompt("SQL> ", multiline=True, prompt_continuation=prompt_continuation,key_bindings=bindings)
                #text = sqlSession.prompt("SQL> ", multiline=is_multi_line, prompt_continuation=prompt_continuation)
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
                        dmlThreadList = []
                        for dbObj in dbObjList:
                            t=workThread(dbObj.exec,(text,rf))
                            dmlThreadList.append(t)
                            t.start()
                            #dbObj.exec(text,rf)
                    elif selPattern.match(text.lower()):
                        for dbObj in dbObjList:
                            dbObj.sel(text,report)
                    elif procPattern.match(text.lower()):
                        if not text.endswith(')'):
                            print('Procedure call must end with ()')
                            continue
                        mt = procPattern.match(text.lower())
                        for dbObj in dbObjList:
                            dbObj.proc(mt.group(1),rf)
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
                self.cmdLogger.write(str(err),'error')
                print(str(err))
                return

