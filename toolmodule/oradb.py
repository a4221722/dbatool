#! /usr/bin/env python
# -*- coding=utf-8 -*-
__author__ = 'luoji'

import cx_Oracle
import datetime
from openpyxl import Workbook
from toolmodule.aes_decryptor import Prpcrypt
import json
from toolmodule.logger import Logger

prpcrypt=Prpcrypt()

class Oradb():
    def __init__(self,name,host,port,sid,username,password,charset):
        if not port:
            port=1521
        self.oraLink=host+':'+str(port)+'/'+sid
        self.name=name
        self.username=username
        self.password=prpcrypt.decrypt(password)
        self.charset=charset

    def checkConnect(self):
        try:
            self.oraConnect=cx_Oracle.connect(self.username,self.password,self.oraLink,encoding=self.charset)
        except Exception as err:
            print(self.name+': '+str(err))
            return False
        else:
            print(self.name+' connect OK.')
            return True

    def exec(self,statement,rf):
        #self.execLogger=Logger(logname=logPath,filename=__file__)
        try:
            self.oraCursor=self.oraConnect.cursor()
            self.oraCursor.execute(statement)
        except Exception as err:
            #self.execLogger.write('#'*ceil(get_terminal_size().columns*0.5)+'\n'+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n'+statement+'\n'+str(err),'error')
            print(self.name+':'+str(err)+'\n'+statement)
            if rf:
                rf.write('\n'+self.name+': '+str(err))
        else:
            #self.execLogger.write('#'*ceil(get_terminal_size().columns*0.5)+'\n'+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n'+statement+'\n'+' statement executed successfully.','error')
            if rf:
                rf.write('\n'+self.name+': statement executed successfully.')
            print(self.name+': statement executed successfully.')

    def sel(self,statement,report):
        try:
            self.oraCursor=self.oraConnect.cursor()
            self.oraCursor.execute(statement)
        except Exception as err:
            print(self.name+':'+str(err)+'\n'+statement)
        else:
            print('\n'+self.name+':')
            header = [format(row[0],'^'+str(min(len(str(row[0]))+4,35))) for row in self.oraCursor.description]
            result=self.oraCursor.fetchall()
            if report == 0:
                print(''.join(header))
                for row in result:
                    print(json.dumps(row))
                    #print('|  '.join(self.maniRt(val) for val in row))
            elif report == 1:
                wb = Workbook(write_only=True)
                ws = wb.create_sheet()
                ws.append(header)
                for row in result:
                    ws.append(row)
                wb.save('./report/'+'_'.join([self.name,datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")])+'.xlsx')

    def maniRt(self,val):
        if isinstance(val,datetime.date):
            return val.strftime("%Y-%m-%d %H:%M:%S.%f")
        else:
            return format(str(val),'>'+str(min(35,len(str(val)))+4))


    def getTabStr(self,schema,tab):
        try:
            selectSql="""select column_name
            ,data_type
            ,data_length
            ,data_precision
            ,nullable
            from dba_tab_columns
            where owner='"""+schema.upper()+"""'
            and table_name='"""+tab.upper()+"'"

            strSet=set()
            self.oraCursor=self.oraConnect.cursor()
            self.oraCursor.execute(selectSql)
            headerList=[row[0] for row in self.oraCursor.description]
            rt=self.oraCursor.fetchall()
            for row in rt:
                strSet.add(row)
        except Exception as err:
            print(str(err))
        else:
            return headerList,strSet

    def getIndStr(self,schema,tab):
        try:
            selectSql="""select a.index_name
            ,a.COLUMN_NAME
            ,a.DESCEND
            ,b.index_type
            ,b.uniqueness
            from dba_ind_columns a,dba_indexes b
            where a.index_owner=b.owner
            and a.index_name=b.index_name
            and a.table_owner='"""+schema.upper()+"""'
            and a.table_name='"""+tab.upper()+"'"

            strSet=set()
            self.oraCursor=self.oraConnect.cursor()
            self.oraCursor.execute(selectSql)
            headerList=[row[0] for row in self.oraCursor.description]
            rt=self.oraCursor.fetchall()
            for row in rt:
                strSet.add(row)
        except Exception as err:
            print(str(err))
        else:
            return headerList,strSet

    def getTabSet(self,schema):
        try:
            selectSql="""select table_name
            from dba_tables
            where owner='"""+schema.upper()+"'"

            tabSet=set()
            self.oraCursor=self.oraConnect.cursor()
            self.oraCursor.execute(selectSql)
            rt=self.oraCursor.fetchall()
            for row in rt:
                tabSet.add(row[0])
        except Exception as err:
            print(str(err))
        else:
            return tabSet

    def getSeqSet(self,schema):
        try:
            selectSql="""select sequence_name
            from dba_sequences
            where sequence_owner='"""+schema.upper()+"'"

            seqSet=set()
            self.oraCursor=self.oraConnect.cursor()
            self.oraCursor.execute(selectSql)
            rt=self.oraCursor.fetchall()
            for row in rt:
                seqSet.add(row[0])
        except Exception as err:
            print(str(err)) 
        else:
            return seqSet

    def commit(self,rf):
        try:
            self.oraConnect.commit()
        except Exception as err:
            if rf:
                rf.write('\n'+self.name+': '+str(err))
            print(str(err))
        else:
            if rf:
                rf.write('\n'+self.name+' commit completely.')
            print(self.name+' commit completely.')

    def rollback(self,rf):
        try:
            self.oraConnect.rollback()
        except Exception as err:
            if rf:
                rf.write('\n'+self.name+': '+str(err))
            print(str(err))
        else:
            if rf:
                rf.write('\n'+self.name+' rollback completely.')
            print(self.name+' rollback completely.')

    def __exit__(self):
        if self.oraConnect:
            self.oraCursor.close()
            self.oraConnect.close()
