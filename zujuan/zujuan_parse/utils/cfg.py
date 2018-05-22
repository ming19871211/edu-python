#!/usr/bin/env python
#-*-coding:utf-8-*-
'''配置类'''
class DBCFG:
    '''Mysql数据库配置'''
    host ="127.0.0.1"
    user ="root"
    passwd="mqm"
    db="tiku_mqm"
    port=3306
    charset="utf8"
    mincached=1
    maxcached=10
    maxconnections=30
class POSTGRE_CFG:
    '''postgreSql数据库配置'''
    host = "localhost"
    #host= "10.10.6.80"
    port = 24967
    user="root"
    passwd="pangu"
    db="ycl_resource"
class MongoDB_CFG:
    '''MongoDB数据库配置'''
    host="127.0.0.1"
    port=27018
    db_name="zujuan"




