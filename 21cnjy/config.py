#!/usr/bin/python
#-*-coding:utf-8-*-
import urlparse
from ConfigParser import ConfigParser
config = ConfigParser()
config.read('21cnjy.cfg')
SELECTION_21CN='21cnjy'
def getCFG(params_name,default=None):
    return config.get(SELECTION_21CN,params_name) if config.has_option(SELECTION_21CN,params_name) else default
#二一组卷网题目查询类型编码对应关系
QUES_QUERY_TYPE = {'question_channel_types':'ques_type','difficult_indexs':'difficulty','exam_types':'exam_type','grade_ids':'grade_id'}
class URL:
    #主页面
    ROOT_URL = getCFG('url_root','https://zujuan.21cnjy.com')
    #学科、学段下载的URL
    SUBJECTS_URL = urlparse.urljoin(ROOT_URL, getCFG('url_subjects_xd','/data/subjects-by-xd?_=%d'))
    #知识点下载URL
    KNOW_URL = urlparse.urljoin(ROOT_URL,getCFG('url_know','/catalog/know-tree?xd=%s&chid=%s&_=%s'))
    KNOW_CHILD_URL = urlparse.urljoin(ROOT_URL,getCFG('url_know_child','/catalog/know-tree?know_id=%s&xd=%s&chid=%s&_=%s'))
    #查询参数URL
    QUERY_PARAM_URL = urlparse.urljoin(ROOT_URL,getCFG('url_query_param','/question/query-params?xd=%s&chid=%s&_=%s'))
    #分析查询题目的url
    QUES_PG_URL = urlparse.urljoin(ROOT_URL,getCFG('url_ques_pg'))
class SQL:
    #查询与更新21cnjy与现有的学科学段关系表
    SELECT_SUBJECT_RELATION = 'select subject_code,xd,subject_zname,course_21 from t_subject_relation_21cnjy WHERE status = 0'
    UPDATE_SUBJECT_RELATION = 'update t_subject_relation_21cnjy set course_21=%s,course_21_name=%s WHERE subject_code=%s'
    #插入二一组卷知识点表
    INSERT_21CNJY_KNOWLED = 'insert into t_21cnjy_knowled_relation(id,name,level,parent_id,cid,sort_no,has_child) VALUES (%s,%s,%s,%s,%s,%s,%s)'
    #插入二一组卷题目类型
    INSERT_21CNJY_TYPE = 'insert into t_ques_type_relation_21cnjy(id,params_type,code_21cnjy,name_21cnjy,subject_code) VALUES(%s,%s,%s,%s,%s)'
    #查询需要爬取题目的知识点ID
    SELECT_KNOWLED_ID = 'select id,name from t_21cnjy_knowled_relation where cid=%s AND has_child=%s AND is_downloaded=%s ORDER BY sort_no'
    #更新知识点的爬取状态
    UPDATE_KNOWLED_DOWNLODED = 'update t_21cnjy_knowled_relation set is_downloaded = %s where id = %s'
    #查询题目查询条件编码与名称
    SELECT_PARAMS_TYPE = 'select subject_code,code_21cnjy,name_21cnjy,code,name from t_ques_type_relation_21cnjy WHERE params_type=%s and status=%s '
    #根据old_id查询题目知识点
    SELECT_POINTS = 'select qid,points from t_ques_21cnjy WHERE old_id=%s'
    #更新题目的知识点
    UPDATE_POINTS= 'UPDATE t_ques_21cnjy SET points=%s WHERE qid=%s'
    #插入新题目
    INSERT_QUES = 'INSERT INTO  t_ques_21cnjy(qid,answer,analyses,cate,cate_name,content,options,sections,points,subject,difficulty,old_id) ' \
                 'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'