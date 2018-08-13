#!/usr/bin/python
#-*-coding:utf-8-*-

import requests
import re
import uuid
import time
from config import URL,SQL,QUES_QUERY_TYPE
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
        self.headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                      "Host":re.findall('^http[s]?://([a-z0-9\.]+?)[/]?$',URL.ROOT_URL)[0], "Referer": URL.ROOT_URL}
        self.session.get(url,headers=self.headers)
        self.sortNo = 0

    def downloadSubject(self,select_sql=SQL.SELECT_SUBJECT_RELATION,update_sql=SQL.UPDATE_SUBJECT_RELATION,
                        subjects_url = URL.SUBJECTS_URL %  Utils.getCurrMilliSecond()):
        '''下载21世纪学科学段，并更新与线网关系对应'''
        response = self.session.get(subjects_url,headers=self.headers)
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
                    response = self.session.get(know_url %(xd,course_21,Utils.getCurrMilliSecond()),headers=self.headers)
                    rs = self.__recursiveKnowled(response.json(),1,subject_code,know_child_url % ('%s',xd,course_21,'%s'))
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
    def __recursiveKnowled(self,knowleds,level,subject_code,url,parentId=None):
        rs = []
        for knowled in knowleds:
            id = knowled['id']
            title = knowled['title']
            hasChild = knowled['hasChild']
            self.sortNo += 1
            sortNO = self.sortNo
            rs.append((id,title,level,parentId,subject_code,sortNO,hasChild))
            if hasChild:
                response = self.session.get(url % (id,Utils.getCurrMilliSecond()),headers=self.headers)
                rs.extend(self.__recursiveKnowled(response.json(),level+1,subject_code,url,id))
        return rs

    def downloadQueryParams(self,select_sql=SQL.SELECT_SUBJECT_RELATION,insert_sql=SQL.INSERT_21CNJY_TYPE,
                            query_param_url=URL.QUERY_PARAM_URL,ques_query_type=QUES_QUERY_TYPE):
        '''下载题目查询参数----如题目类型、难度等等'''
        pg = PostgreSql()
        count=0
        try:
            for row in pg.getAll(select_sql):
                try:
                    subject_code, xd, subject_zname, course_21 = row
                    insert_params=[]
                    response = self.session.get(query_param_url % (xd, course_21, Utils.getCurrMilliSecond()),headers=self.headers)
                    for param_type,values in response.json().iteritems():
                        if not ques_query_type.has_key(param_type):
                            continue
                        for code,name in values.iteritems():
                            count+=1
                            id = count
                            insert_params.append((id, ques_query_type[param_type],code,name,subject_code))
                    if insert_params: pg.batchExecute(insert_sql,insert_params)
                    pg.commit()
                    logger.info(u'完成二一组卷网（学段:%s,学科:%s,线上学科名称:%s,线上学科代码:%s）查询参数的导入，导入参数的数量:%d，所有学科处理总数%d',
                                xd, course_21, subject_zname, subject_code, len(insert_params),count)
                except Exception as e:
                    logger.exception(u'二一组卷网（学段:%s,学科:%s,线上学科名称:%s,线上学科代码:%s）查询参数的导入异常',
                                     xd, course_21, subject_zname, subject_code)
                    pg.rollback()
        finally:
            pg.close()

    def downloadQuestions(self,ques_type='',ques_pg_url=URL.QUES_PG_URL,select_knowled_id=SQL.SELECT_KNOWLED_ID,
                          select_subject_sql=SQL.SELECT_SUBJECT_RELATION,select_params_type=SQL.SELECT_PARAMS_TYPE,
                          update_knowled_downloded = SQL.UPDATE_KNOWLED_DOWNLODED):
        '''按知识点下载题目'''
        pg = PostgreSql()
        try:
            #获取题目类型信息
            ques_type_dic={}
            for row_ques_types in pg.getAll(select_params_type,('ques_type',1)):
                subject_code, code_21cnjy, name_21cnjy, code,name = row_ques_types
                #按学科类型分组
                if not ques_type_dic.has_key(subject_code): ques_type_dic[subject_code] = {}
                #具体学科的编码类型信息
                ques_type_dic[subject_code][code_21cnjy] = {'code_21cnjy':code_21cnjy,'name_21cnjy':name_21cnjy,'code':code,'name':name}
            #获取学段信息
            for row in pg.getAll(select_subject_sql):
                try:
                    subject_code, xd, subject_zname, course_21 = row
                    self.__downloadQuestionsBySubject(row,pg,ques_pg_url,ques_type_dic[subject_code],ques_type,select_knowled_id,update_knowled_downloded)
                except Exception as e:
                    logger.exception(u'二一组卷网（学段:%s,学科:%s,线上学科名称:%s,线上学科代码:%s）题目导入异常',
                                     xd, course_21, subject_zname, subject_code)
                    pg.rollback()
                    raise e
        finally:
            pg.close()

    def __downloadQuestionsBySubject(self,subject_row,pg,ques_pg_url,ques_type_dic,ques_type='',
                                     select_knowled_id=SQL.SELECT_KNOWLED_ID,update_knowled_downloded = SQL.UPDATE_KNOWLED_DOWNLODED):
        '''按学段下载题目，subject_row:为学段信息数组依次为subject_code, xd, subject_zname, course_21；pg:为pgsql数据对象；
        ques_type_dic为本学科下题目类型的信息结构{codeId:{'code_21cnjy':code_21cnjy,'name_21cnjy':name_21cnjy,'code':code,'name':name}}'''
        subject_code, xd, subject_zname, course_21 = subject_row
        logger.info(u'开始学段(%s-%s)题目爬取', subject_code,subject_zname)
        #查询知识点
        knowled_id = ''
        #查询需要爬取的知识点
        update_count = 0
        insert_count = 0
        ignore_count = 0
        for row in pg.getAll(select_knowled_id,(subject_code,False,False)):
            try:
                i,j,k=self.__downloadQuestionsByKnowled(row,subject_row,pg,ques_pg_url,ques_type_dic,ques_type,update_knowled_downloded)
                update_count += i
                insert_count += j
                ignore_count += k
            except Exception as e:
                logger.exception(u'下载知识点(%s-%s)题目异常:%s',row[0],row[1],e.message)
        logger.info(u'完成学段(%s-%s)题目爬取,爬取题型:%s,更新数量:%d，新增数量:%d,忽略数量:%d',
                    subject_code, subject_zname, ques_type if ques_type else '全部题型',
                    update_count, insert_count, ignore_count)

    def __downloadQuestionsByKnowled(self,know_row,subject_row,pg,ques_pg_url,ques_type_dic,ques_type='',
                                     update_knowled_downloded = SQL.UPDATE_KNOWLED_DOWNLODED):
        '''按最后一层知识点下载题目'''
        knowled_id,knowled_name=know_row
        subject_code, xd, subject_zname, course_21 = subject_row
        headers = {'X-Requested-With':'XMLHttpRequest'}
        for key,value in self.headers.iteritems():headers[key]=value
        url=ques_pg_url % (xd, course_21, knowled_id, ques_type, 1, Utils.getCurrMilliSecond())
        response = self.session.get(url,headers=headers)
        rs = response.json()
        if rs['code'] != 0: #判断请求结果是否正常
            logger.error(u'知识点:%s,知识点名称:%s,学段:%s,学段名称:%s,分页:%d,请求信息异常,异常信息:%s',
                         knowled_id, knowled_name, subject_code, subject_zname, 1, rs['msg'])
            raise Exception(u'分页请求题目结果异常，请求url：%s' % url)
        # 获取统计
        total = int(rs['data']['total'])
        update_count = 0
        insert_count = 0
        ignore_count = 0
        if total :
            #处理题目
            i,j,k= self.__batchQuesttions( rs['data']['questions'],know_row,subject_row,ques_type_dic,pg)
            update_count += i
            insert_count += j
            ignore_count += k
            page_count=total/10+(1 if total%10 else 0)
            for page in range(2,page_count+1):
                next_url= ques_pg_url % (xd, course_21, knowled_id, ques_type, page, Utils.getCurrMilliSecond())
                response_next = self.session.get(next_url,headers=headers)
                # 处理题目
                rs_next = response_next.json()
                if rs_next['code'] !=0:  #判断请求结果是否正常
                    logger.error(u'知识点:%s,知识点名称:%s,学段:%s,学段名称:%s,分页:%d,请求信息异常,异常信息:%s',
                                knowled_id,knowled_name,subject_code,subject_zname,page,rs_next['msg'])
                    raise Exception(u'分页请求题目结果异常，请求url：%s'% next_url)
                i,j,k= self.__batchQuesttions(rs_next['data']['questions'], know_row, subject_row,ques_type_dic, pg)
                update_count += i
                insert_count += j
                ignore_count += k
        try:
            # 标记该知识点数据已爬取完成
            pg.execute(update_knowled_downloded,(True,knowled_id))
            pg.commit()
        except  Exception as e:
            logger.exception(u'更新知识点下载状态为已完成异常,知识点(%s:%s),学科(%s:%s)',knowled_id,knowled_name,subject_code,subject_zname)
            pg.rollback()
        logger.info(u'知识点:%s,知识点名称:%s,学段:%s,学段名称:%s--题目爬取完成,爬取题型:%s,爬取总数:%d,实际更新数量:%d，新增数量:%d,忽略题目数量:%d',
                    knowled_id,knowled_name,subject_code,subject_zname,ques_type if ques_type else '全部题型',total,update_count,insert_count,ignore_count)
        return (update_count,insert_count,ignore_count)

    def __batchQuesttions(self,questions,know_row,subject_row,ques_type_dic,pg,select_sql=SQL.SELECT_POINTS,
                          update_sql=SQL.UPDATE_POINTS,insert_sql=SQL.INSERT_QUES):
        try:
            subject_code, xd, subject_zname, course_21 = subject_row
            point = {'code':know_row[0],'name':know_row[1]}
            insert_params=[]
            update_params=[]
            ignore_count = 0
            for ques in questions:
                rs = self.__getQuestionDetail(ques,ques_type_dic)
                if not rs:
                    ignore_count +=1
                    continue
                qid, answer, analyses, cate, cate_name, content, options, difficulty, old_id = rs
                #根据qid获取题目详情
                row= pg.getOne(select_sql,(old_id,))
                if row:
                    qid, points = row
                    flag = True #默认需要添加知识点ID
                    for p in points:
                        if p['code']== know_row[0]:
                            #如果知识点ID存在就不添加
                            flag = False
                            break
                    if flag:
                        points.append(point)
                        # 增加题目的知识点ID
                        update_params.append((Utils.toJson(points),qid))
                else:
                    sections = None
                    insert_params.append((qid,answer,analyses,cate,cate_name,content,options,sections,Utils.toJson([point]),subject_code,difficulty,old_id))
            if update_params: pg.batchExecute(update_sql,update_params)
            if insert_params: pg.batchExecute(insert_sql,insert_params)
            pg.commit()
            return (len(update_params),len(insert_params),ignore_count)
        except Exception as e:
            logger.exception(u'批量处理题目异常,学科(%s-%s),异常信息:%s',subject_code,subject_zname,e.message)
            pg.rollback()
            raise e

    def __getQuestionDetail(self,ques,ques_type_dic):
        '''获取题目详情'''
        code_21cnjy = int(ques['question_channel_type'])
        if ques_type_dic.has_key(code_21cnjy) and code_21cnjy == 1:
            try:
                qid = str(uuid.uuid1())
                old_id = ques['question_id']
                cate = ques_type_dic[code_21cnjy]['code']
                cate_name = ques_type_dic[code_21cnjy]['name']
                content = ques['question_text']
                options = []
                if not ques.has_key('options') or not ques['options'] or not isinstance(ques['options'],dict):
                    return None
                for key,value in ques['options'].iteritems():
                    options.insert(ord(key) - ord('A'), value)
                options = Utils.toJson(options)
                difficulty = ques['difficult_index']
                answer = ques['answer']
                analyses = ques['explanation']
                return qid,answer,analyses,cate,cate_name,content,options,difficulty,old_id
            except Exception as e:
                logger.exception(u'单个题目解析异常:%s,题目内容：%s',e.message,Utils.toJson(ques))
                raise e
        else:
            raise Exception(u'题型暂时无法解析')

if __name__ == '__main__':
    zj21cnjy = ZJ21cnjy()
    zj21cnjy.downloadQuestions(1)