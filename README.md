DBATool V1.0

#使用方法
source bin/activate

python dbatool.py

## 支持的操作
* 管理实例: inst
* 执行sql，可以生成excel: sql
* 对比schema和表结构: check

## 生成excel的方法：
进入sql界面: spool on;
关闭生成excel的功能: spool off;
以上两个命令不要漏掉分号

## dml生成操作日志：
进入sql界面: record on;
record off;关闭
