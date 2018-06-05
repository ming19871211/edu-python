#!/usr/bin/python
#-*-coding:utf-8-*-
import MySQLdb #引入mysql数据库驱动包
import MySQLdb.cursors
import psycopg2 #引入postgreSql数据库驱动包
import psycopg2.extras
from  DBUtils.PooledDB import PooledDB #引入连接池操作
from pymongo import MongoClient #引入mongodb数据库驱动包
from cfg import DBCFG,POSTGRE_CFG,MongoDB_CFG
''''' 
数据库操作工具类
Created on 2017年11月9日  
@author: meiqiming 
'''  
class Mysql(object):
    '''Mysql操作对象'''
    #连接池对象
    __pool = None
    def __init__(self):
      self.__conn= self.__getConn()
      self.__cur=self.__conn.cursor()
      self.__cur_dic = self.__conn.cursor(MySQLdb.cursors.DictCursor)

    @staticmethod
    def __getConn():
        """ 静态方法，从连接池中取出连接 """  
        if Mysql.__pool is None:
            __pool=PooledDB(creator=MySQLdb,mincached=DBCFG.mincached,maxcached=DBCFG.maxcached,maxconnections=DBCFG.maxconnections,
            host=DBCFG.host, port=DBCFG.port, user=DBCFG.user, passwd=DBCFG.passwd,  
            db=DBCFG.db,use_unicode=False,charset=DBCFG.charset)

        return __pool.connection()
        
    def close(self):
        """关闭当前连接"""
        self.__cur.close()
        self.__cur_dic.close()
        self.__conn.close()

    def execute(self,sql,params=None):
        '''执行SQL'''      
        return self.__cur.execute(sql,params)        
    
    def batchExecute(self,sql,params):
        '''执行批处理SQL\n
        @sql 模板SQL语句 \n
        @params 列表的元组集合
        '''
        return self.__cur.executemany(sql, params) 

    def getAll(self,sql,param=None,isdic=False):
        '''执行查询获取所有结果'''
        cur = self.__cur_dic if isdic else self.__cur
        count = cur.execute(sql,param)  
        if count:
            return cur.fetchall()

    def getOne(self,sql,param=None):  
        '''执行查询获取第一条查询结果'''
        count = self.__cur.execute(sql,param)  
        if count:  
            return  self.__cur.fetchone()[0] 
        
    def getMany(self,sql,num,param=None):  
        """  执行查询，并取出num条结果 """       
        count = self.__cur.execute(sql,param)  
        if count:  
            return  self.__cur.fetchmany(num)  

    def getIteratorFastAll(self,sql,totalNum,param=None,num=1000,isdic=False):
        '''获取分页数据的迭代器, 每次分页num条数据        
        @param 值必须为字典类型 \n 
        @isdic 返回值的记录否为字典类型，否则为元组类型 \n 
        SQL语句类似于如下写法 \n
        SELECT autoId,OriginalID,Answer,Analysis,Difficulty,difficultyValue, 
        Content,KnowledgeDetail,`Comment`,zujuan_number,`Options`, 
        thirdkonwledgeid,secondknowledgeid,firstknowledgeid,courseId, 
        subject_code,typeflag,typeid,thirdknowledgename 
        FROM k12_tiku_details 
        WHERE  autoId >=(select autoId from k12_tiku_details limit %(start)s,1) limit %(num)s
        '''
        if param is None:
            param = {}
        for pg in range(totalNum/num+1):
            param['start']=pg*num
            param['num']=num
            yield self.getAll(sql,param,isdic)

    def getIteratorAll(self,sql,param=None,num=1000):
        '''获取分页数据的迭代器，每次分页num条数据\n
        当数据量很大时此方法效率低下'''
        #计算分页
        totalNum = self.getOne("select count(*) from (%s) ttt " % sql,param)
        if totalNum:
            for pg in range(totalNum/num+1):
                yield self.getPg(sql,pg+1,num,param)    

    def getPg(self,sql,pg,num,param=None):
        '''执行分页查询，获取结果集合\n
        当pg与num较大时，此方法效率低下'''
        sql = sql + " LIMIT %d,%d " %((pg-1)*num,num)
        return self.getAll(sql,param)

    def begin(self):
        '''设置开启事务'''
        self.__conn.begin()
    def cancel(self):
        '''设置关闭事务'''
        self.__conn.cancel()

    def commit(self):
        '''提交事务 '''
        self.__conn.commit()

    def rollback(self):
        """回滚数据"""
        self.__conn.rollback()


class PostgreSql(object):
    '''PostgreSql操作对象'''

    def __init__(self):
      self.__conn= self.__getConn()
      self.__cur=self.__conn.cursor()
      self.__cur_dic = self.__conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    @staticmethod
    def __getConn():
        """ 静态方法，获取连接 """  
        conn=psycopg2.connect(database=POSTGRE_CFG.db,user=POSTGRE_CFG.user,password=POSTGRE_CFG.passwd,host=POSTGRE_CFG.host,port=POSTGRE_CFG.port)
        return conn
        
    def close(self):
        """关闭当前连接"""
        self.__cur.close()
        self.__cur_dic.close()
        self.__conn.close()

    def execute(self,sql,params=None):
        '''执行SQL'''      
        return self.__cur.execute(sql,params)        
    
    def batchExecute(self,sql,params):
        '''执行批处理SQL\n
        @sql 模板SQL语句 \n
        @params 列表的元组集合
        '''
        return self.__cur.executemany(sql, params) 

    def getAll(self,sql,param=None,isdic=False):
        '''执行查询获取所有结果'''
        cur = self.__cur_dic if isdic else self.__cur
        cur.execute(sql,param)
        return cur.fetchall()

    def getOne(self,sql,param=None):  
        '''执行查询获取第一条查询结果'''
        self.__cur.execute(sql,param)
        return  self.__cur.fetchone()
        
    def getMany(self,sql,num,param=None):  
        """  执行查询，并取出num条结果 """       
        self.__cur.execute(sql,param)
        return  self.__cur.fetchmany(num)

    def getIteratorAll(self,sql,param=None,num=1000):
        '''获取分页数据的迭代器，每次分页num条数据\n
        当数据量很大时此方法效率低下'''
        #计算分页
        totalNum = self.getOne("select count(*) from (%s) ttt " % sql,param)
        if totalNum:
            for pg in range(totalNum/num+1):
                yield self.getPg(sql,pg+1,num,param)    

    def getPg(self,sql,pg,num,param=None):
        '''执行分页查询，获取结果集合\n
        当pg与num较大时，此方法效率低下'''
        sql = sql + " LIMIT %d OFFSET %d " %(num,(pg-1)*num)
        return self.getAll(sql,param)

    def begin(self):
        '''设置开启事务'''
        self.__conn.begin()
    def cancel(self):
        '''设置关闭事务'''
        self.__conn.cancel()

    def commit(self):
        '''提交事务 '''
        self.__conn.commit()

    def rollback(self):
        """回滚数据"""
        self.__conn.rollback()

class MongoDB(object):
    '''mongoDB操作对象'''
    def __init__(self,host=MongoDB_CFG.host,port=MongoDB_CFG.port):
        self.__conn = self.__getConn(host,port)
        self.__db = self.__conn[MongoDB_CFG.db_name]
    @staticmethod
    def __getConn(host=MongoDB_CFG.host,port=MongoDB_CFG.port):
        """ 静态方法，获取连接 """
        conn = MongoClient(host,port)
        return conn
    def getCollectionNames(self):
        '''获取所有非系统集合'''
        return self.__db.collection_names(include_system_collections=False)
    def getCollection(self,collectionName):
        '''获取集合（表）'''
        return self.__db[collectionName]

