#!/usr/bin/python
#-*-coding:utf-8-*-
import MySQLdb #引入mysql数据库驱动包
import MySQLdb.cursors
from  DBUtils.PooledDB import PooledDB #引入连接池操作
import cx_Oracle
from cfg import DBCFG
''''' 
数据库操作工具类
Created on 2017年11月9日  
@author: meiqiming 
'''
class Oracle(object):
    def __init__(self,user=DBCFG.orcl_user,password=DBCFG.orcl_passwd,orclpdb=DBCFG.orcl_pdb):
        self.__conn = self.__getConn(user,password,orclpdb)
        self.__cur = self.__conn.cursor()

    @staticmethod
    def __getConn(user,password,orclpdb):
        return cx_Oracle.connect(user, password,orclpdb)

    def getOne(self,sql,param=None):
        '''执行查询获取第一条查询结果'''
        if param:
            count = self.__cur.execute(sql,param)
        else:
            count = self.__cur.execute(sql)
        if count:
            return  self.__cur.fetchone()
    def getAll(self,sql,param=None,isdic=False):
        '''执行查询获取所有结果'''
        cur = self.__cur_dic if isdic else self.__cur
        count = cur.execute(sql,param)
        if count:
            return cur.fetchall()
    def batchExecute(self,sql,params):
        '''执行批处理SQL\n
        @sql 模板SQL语句 \n
        @params 列表的元组集合
        '''
        return self.__cur.executemany(sql, params)
    def commit(self):
        '''提交事务 '''
        self.__conn.commit()
    def cancel(self):
        '''设置关闭事务'''
        self.__conn.cancel()
    def close(self):
        """关闭当前连接"""
        self.__cur.close()
        self.__conn.close()

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

