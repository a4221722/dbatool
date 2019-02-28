# DBATool V1.1
这是一个多实例db管理工具，出发点是对多套数据库做集中化的命令行管理.
python 3.7.1

# 使用方法
source bin/activate

python dbatool.py

## 支持的操作
* 管理实例: inst
* 执行sql，可以生成excel: sql
* 对比schema和表结构: check

## 生成excel的方法：
进入sql界面: spool on;
##关闭生成excel的功能:
spool off;
以上两个命令不要漏掉分号

## dml生成操作日志：
进入sql界面: record on;
record off;关闭

# 部署
## 创建目录
````
mkdir log
mkdir db
````
## 建表
````
cd db
sqlite3 dba.db
CREATE TABLE mysql_instances(id integer primary key autoincrement,name varchar(10),host varchar(16),port integer,username varchar(30),password varchar(100), charset varchar(10), "group" varchar(30), constraint uk_my unique(host,port));

CREATE TABLE oracle_instances(id integer primary key autoincrement,name varchar(10),host varchar(16),port integer,sid varchar(10),username varchar(30),password varchar(100) , charset varchar(10), "group" varchar(30),constraint uk1_ora unique (host,port,sid),constraint uk2_ora unique(name));
````
