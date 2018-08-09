#!/usr/bin/python
#-*-coding:utf-8-*-

import requests
import time
from config import URL,SQL
from utils.SqlUtil import PostgreSql
from utils import LoggerUtil,Utils
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# 日志
logger = LoggerUtil.getLogger(__name__)

class ZJ21cnjy:
    '''组卷21世纪网题目分析类'''
    def __init__(self, url=URL.ROOT_URL):
        self.session = requests.Session()
        self.session.get(url)
        self.sortNo = 0

    def downloadSubject(self,select_sql=SQL.SELECT_SUBJECT_RELATION,update_sql=SQL.UPDATE_SUBJECT_RELATION,
                        subjects_url = URL.SUBJECTS_URL %  Utils.getCurrMilliSecond()):
        '''下载21世纪学科学段，并更新与线网关系对应'''
        response = self.session.get(subjects_url)
        zj21cnjy_subject= response.json()
        pg = PostgreSql()
        try:
            update_params=[]
            for row in pg.getAll(select_sql):
                subject_code, xd, subject_zname,course_21 = row
                if course_21:continue
                course_21_name = None
                for key,value in zj21cnjy_subject[str(xd)].iteritems():
                    value_temp = value if  value != u'政治思品' else u'政治'
                    if subject_zname.find(value_temp) > -1:
                        course_21 = key
                        course_21_name = value
                if course_21:
                    update_params.append((course_21,course_21_name,subject_code))
            if update_params: pg.batchExecute(update_sql,update_params)
            pg.commit()
            logger.info(u'完成21cnjy与线网学科学段对应关系更新,更新数量：%d',len(update_params))
        except Exception as e:
            logger.exception(u'21cnjy与线网学科学段对应关系更新出现异常，异常信息:%s',e.message)
            pg.rollback()
        finally:
            pg.close()

    def downloadKnowled(self,select_sql=SQL.SELECT_SUBJECT_RELATION,inser_konw_sql=SQL.INSERT_21CNJY_KNOWLED,
                        know_url=URL.KNOW_URL,know_child_url=URL.KNOW_CHILD_URL):
        '''下载知识点'''
        pg = PostgreSql()
        try:
            for row in pg.getAll(select_sql):
                try:
                    subject_code, xd, subject_zname,course_21 = row
                    response = self.session.get(know_url %(xd,course_21,Utils.getCurrMilliSecond()))
                    rs = self.recursiveKnowled(response.json(),1,subject_code,know_child_url % ('%s',xd,course_21,'%s'))
                    if rs: pg.batchExecute(inser_konw_sql,rs)
                    pg.commit()
                    logger.info(u'完成二一组卷网（学段:%s,学科:%s,线上学科名称:%s,线上学科代码:%s）知识点的导入，导入知识点数量:%d',
                                xd,course_21,subject_zname,subject_code,len(rs))
                except Exception as e:
                    logger.exception(u'二一组卷网（学段:%s,学科:%s,线上学科名称:%s,线上学科代码:%s）知识点的导入异常',
                                xd, course_21, subject_zname, subject_code)
                    pg.rollback()
        finally:
            pg.close()
    def recursiveKnowled(self,knowleds,level,subject_code,url,parentId=None):
        rs = []
        for knowled in knowleds:
            id = knowled['id']
            title = knowled['title']
            hasChild = knowled['hasChild']
            self.sortNo += 1
            sortNO = self.sortNo
            rs.append((id,title,level,parentId,subject_code,sortNO,hasChild))
            if hasChild:
                response = self.session.get(url % (id,Utils.getCurrMilliSecond()))
                rs.extend(self.recursiveKnowled(response.json(),level+1,subject_code,url,id))
        return rs
if __name__ == '__main__':
    zj21cnjy = ZJ21cnjy()
    zj21cnjy.downloadKnowled()
