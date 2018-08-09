#!/usr/bin/python
#-*-coding:utf-8-*-
import urlparse
from ConfigParser import ConfigParser
config = ConfigParser()
config.read('21cnjy.cfg')
SELECTION_21CN='21cnjy'
def getCFG(params_name,default=None):
    return config.get(SELECTION_21CN,params_name) if config.has_option(SELECTION_21CN,params_name) else default

class URL:
    ROOT_URL = getCFG('url_root','https://zujuan.21cnjy.com')
    SUBJECTS_URL = urlparse.urljoin(ROOT_URL, getCFG('url_subjects_xd','/data/subjects-by-xd?_=%d'))
    KNOW_URL = urlparse.urljoin(ROOT_URL,getCFG('url_know','/catalog/know-tree?xd=%s&chid=%s&_=%s'))
    KNOW_CHILD_URL = urlparse.urljoin(ROOT_URL,getCFG('url_know_child','/catalog/know-tree?know_id=%s&xd=%s&chid=%s&_=%s'))
class SQL:
    #查询与更新21cnjy与现有的学科学段关系表
    SELECT_SUBJECT_RELATION = 'select subject_code,xd,subject_zname,course_21 from t_subject_relation_21cnjy WHERE status = 0'
    UPDATE_SUBJECT_RELATION = 'update t_subject_relation_21cnjy set course_21=%s,course_21_name=%s WHERE subject_code=%s'
    #插入二一组卷知识点表
    INSERT_21CNJY_KNOWLED = 'insert into t_21cnjy_knowled_relation(id,name,level,parent_id,cid,sort_no,has_child) VALUES (%s,%s,%s,%s,%s,%s,%s)'

