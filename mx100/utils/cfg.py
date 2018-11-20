#!/usr/bin/env python
#-*-coding:utf-8-*-
'''配置类'''
class DBCFG:
    '''Mysql数据库配置'''
    host ="yd-mysql.talkedu.cn"
    user ="root"
    passwd="yd@shiping"
    db="hxypc"
    port=3306
    charset="utf8"
    mincached=1
    maxcached=3
    maxconnections=3
    '''Oracle数据库配置'''
    orcl_user = 'mx100'
    orcl_passwd = 'mx100mx100'
    orcl_pdb = "127.0.0.1:1521/orcl"



