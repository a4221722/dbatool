#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'
from toolmodule.args import args
import sqlite3
from settings import *
from toolmodule.oradb import Oradb
from toolmodule.mydb import Mydb
from toolmodule.logger import Logger


objMap = {
    'oracle':Oradb,
    'mysql':Mydb
}

class Check():
    def __init__(self):
        self._dbConnect = sqlite3.connect(dbPath)
        self._dbCursor = self._dbConnect.cursor()
        self.dbObjList=''
        self.cmdLogger=Logger(logname=logname,filename=__file__)

    def _getDbObj(self,**kwargs):
        typ=kwargs['typ']
        #检查是否指定两个实例
        if (not kwargs['fstid'] and not kwargs['fstname']) or (not kwargs['secid'] and not kwargs['secname']):
            print('Two instances must be assigned!')
            return

        if (kwargs['fstid'] and kwargs['fstname']) or (kwargs['secid'] and kwargs['secname']):
            print('Only one argument for each instance.')
            return

        #创建两个数据连接对象
        whereStList=[]
        if kwargs['fstid']:
            whereStList.append(' where id in ('+str(kwargs['fstid'])+')')
        if kwargs['fstname']:
            whereStList.append(" where name in('"+kwargs['fstname']+"')")
        if kwargs['secid']:
            whereStList.append(' where id in ('+str(kwargs['secid'])+')')
        if kwargs['secname']:
            whereStList.append(" where name in('"+kwargs['secname']+"')")

        colList = [col for col in colMap[tabMap[typ]] if col.lower() in connectList]
        connList = []
        for whereSt in whereStList:
            selectSql='select '+','.join(str(col) for col in colList)+' from '+tabMap[typ]+whereSt
            self._dbCursor.execute(selectSql)
            result=self._dbCursor.fetchall()
            connList.append(result[0])

        if len(connList)<2:
            print('at least one instance do not exist!')
            return

        #使用取到的数据库连接信息，分别创建对应的数据对象，连接正常的放到列表里
        self.dbObjList = []
        for colList in connList:
            dbObj = objMap[typ](*colList)
            connectSt=dbObj.checkConnect()
            if connectSt:
                self.dbObjList.append(dbObj)
            else:
                continue

    @args('-t',dest='typ',required=True, action='store',
         choices={'oracle','mysql'},default='oracle',
         help='instance type')
    @args('-d',dest='fstid',action='store',
         type=int,help='first instance id')
    @args('-n',dest='fstname',action='store',
         help='first instance name')
    @args('-D',dest='secid',action='store',
         type=int,help='second instance id')
    @args('-N',dest='secname',action='store',
         help='second instance name')
    @args('-T',dest='tablename',required=True,action='store',nargs='*',
          help=' table list. use : between two different tables')
    #@args('-s',dest='schemaname',action='store',nargs='*',
    #     help=' schema list')

    #对比两个实例同名表的结构
    def table(self,**kwargs):

        #表名格式应该为 schema.table
        for tn in kwargs['tablename']:
            if tn.find('.') == -1:
                print('format must be schema.table')
                return
        if not self.dbObjList:
            self._getDbObj(**kwargs)

        for tn in kwargs['tablename']:
            if tn.find(':') > 0:
                tnList=tn.split(':')
                schema0,tab0=tnList[0].split('.')
                schema1,tab1=tnList[1].split('.')
            else:
                schema0,tab0=tn.split('.')
                schema1,tab1=tn.split('.')
            headList0,tabStr0=self.dbObjList[0].getTabStr(schema0,tab0)
            headList1,tabStr1=self.dbObjList[1].getTabStr(schema1,tab1)

            print('\n'+tn.upper()+': ')
            if not tabStr0:
                print('\n   table '+schema0+'.'+tab0+' does not exist in '+self.dbObjList[0].name)
                continue
            if not tabStr1:
                print('\n   table '+schema1+'.'+tab1+' does not exist in '+self.dbObjList[1].name)
                continue

            if tabStr0 == tabStr1:
                print('\n   '+tn+' are the same on both sides.')
            else:
                print('\n   '+self.dbObjList[0].name+'.'+schema0+'.'+tab0+': ')
                print(' '.join(format(str(val),'^30') for val in headList0))
                for row in (tabStr0-tabStr1):
                    print('|'.join(format(str(val),'>30') for val in row))
                print('\n   '+self.dbObjList[1].name+'.'+schema1+'.'+tab1+': ')
                print(' '.join(format(str(val),'^30') for val in headList1))
                for row in (tabStr1-tabStr0):
                    print('|'.join(format(str(val),'>30') for val in row))

            headList0,tabStr0=self.dbObjList[0].getIndStr(schema0,tab0)
            headList1,tabStr1=self.dbObjList[1].getIndStr(schema1,tab1)

            if tabStr0 == tabStr1:
                print('   '+tn+' has same indexes on both sides.')
            else:
                print('\n   '+self.dbObjList[0].name+'.'+schema0+'.'+tab0+': ')
                print(' '.join(format(str(val),'^30') for val in headList0))
                for row in (tabStr0-tabStr1):
                    print('|'.join(format(str(val),'>30') for val in row))
                print('\n   '+self.dbObjList[1].name+'.'+schema1+'.'+tab1+': ')
                print(' '.join(format(str(val),'^30') for val in headList1))
                for row in (tabStr1-tabStr0):
                    print('|'.join(format(str(val),'>30') for val in row))


    @args('-t',dest='typ',required=True, action='store',
         choices={'oracle','mysql'},default='oracle',
         help='instance type')
    @args('-d',dest='fstid',action='store',
         type=int,help='first instance id')
    @args('-n',dest='fstname',action='store',
         help='first instance name')
    @args('-D',dest='secid',action='store',
         type=int,help='second instance id')
    @args('-N',dest='secname',action='store',
         help='second instance name')
    @args('-s',dest='schemaname',required=True,action='store',nargs='*',
          help=' schema list. use : between different schemas')
    def schema(self,**kwargs):
        self._getDbObj(**kwargs)
        #检查输入的schemaname参数格式，如果带有:则代表两个不同schema的对比
        for schemaComp in kwargs['schemaname']:
            if schemaComp.find(':')>0:
                schemaCompList = schemaComp.split(':')
                schema0=schemaCompList[0]
                schema1=schemaCompList[1]
            else:
                schema0=schemaComp
                schema1=schemaComp
            tabSet0=self.dbObjList[0].getTabSet(schema0)
            tabSet1=self.dbObjList[1].getTabSet(schema1)
            tabList = [schema0+'.'+val+':'+schema1+'.'+val for val in (tabSet0 | tabSet1)]
            tabKwargs={key:val for key,val in kwargs.items() if key != 'schemaname'}
            tabKwargs['tablename']=tabList
            print('\n'+'='*25+'TABLE'+'='*25)
            self.table(**tabKwargs)

            if kwargs['typ'] == 'oracle':
                print('\n'+'='*25+'SEQUENCE'+'='*25)
                seqSet0=self.dbObjList[0].getSeqSet(schema0)
                seqSet1=self.dbObjList[1].getSeqSet(schema1)

                if seqSet0 == seqSet1:
                    print('\n   '+schema0+' and '+schema1+' has same sequences on both sides.')
                else:
                    print('\n   '+self.dbObjList[0].name+'.'+schema0+':')
                    for seq in (seqSet0-seqSet1):
                        print(format(seq,'>40'))
                    print('\n   '+self.dbObjList[1].name+'.'+schema1+':')
                    for seq in (seqSet1-seqSet0):
                        print(format(seq,'>40'))

