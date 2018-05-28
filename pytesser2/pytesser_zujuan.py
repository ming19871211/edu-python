#!/usr/bin/python
#-*-coding:utf-8-*-


import requests
import os
import urlparse
import json
from utils.SqlUtil import PostgreSql
from utils import LoggerUtil,Utils
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
logger = LoggerUtil.getLogger(__name__)

SELECT_SQL = 'SELECT qid,answer FROM T_QUES_ZUJUAN_EX WHERE cate=1 AND subject= %s AND qid > %s ORDER BY seq ASC LIMIT %s '
UPDATE_SQL = 'UPDATE T_QUES_ZUJUAN_EX SET  choice_answer = %s WHERE qid = %s'
UPDATE_STATUS_SQL = 'UPDATE T_QUES_ZUJUAN_EX SET  status = %s WHERE qid = %s'
ROWS = 1000
rootImagPath = '/data/meiqiming/data/zj_image_new'

OPTIONS ={'A':[],'B':[],'C':[],'D':[],'E':[]}

def init():
    for parent, dir_names, file_names in os.walk('data'):
        for file_name in file_names:
            for key,values in OPTIONS.items():
                if file_name.startswith(key):
                    values.append(Utils.getFileMD5(os.path.join(parent, file_name)))
init()
print OPTIONS
def getTextByImageUrl2(url):
    data = requests.get(url).content
    X = Utils.getStrMD5(data)
    z = u'未知'
    count = 0
    for key, values in OPTIONS.items():
        if X in values:
            count += 1
            z = key
    if count > 1 :
        raise Exception('MD5值匹配出现异常')
    if z == u'未知':
        print(url,X)
        raise Exception('未知不能识别的图片')
    return z

def getFilename(url, root_path=rootImagPath):
    url_path = urlparse.urlsplit(url)
    return os.path.join(root_path, url_path.path[1:])
def getTextByImageUrl(url):
    fileName = getFilename(url)
    X = Utils.getFileMD5(fileName)
    z = u'未知'
    count = 0
    for key, values in OPTIONS.items():
        if X in values:
            count += 1
            z = key
    if count > 1:
        raise Exception('MD5值匹配出现异常')
    if z == u'未知':
        # print(url, X)
        raise Exception('未知不能识别的图片')
    return z

def getZjImg(str):
    return re.findall(u'[\"|\'](https?://[a-z0-9A-z][a-z0-9A-z\.]+[a-z0-9A-z]/.*?)[\\\]?[\"|\']', str)
def findImags(subject):
    rows = ROWS
    try:
        pg = PostgreSql()
        flag = True
        count = 0
        qid = '0'

        err_count = 0
        while flag:
            try:
                flag = False
                update_params = []
                update_err_params = []
                for row in pg.getAll(SELECT_SQL,(subject,qid,rows)):
                    flag =True
                    qid = row[0]
                    url = getZjImg(row[1])[0]
                    try:
                        choice_answer = getTextByImageUrl2(url)
                        answer_arr = []
                        answer_arr.append(choice_answer)
                        update_params.append((json.dumps(answer_arr,ensure_ascii=False),qid))
                        count += 1
                    except Exception as ex:
                        err_count +=1
                        update_err_params.append((-1,qid))
                        logger.exception('异常的题目ID:%s,url:%s',qid,url)
                if update_params: pg.batchExecute(UPDATE_SQL,update_params)
                if update_err_params: pg.batchExecute(UPDATE_STATUS_SQL,update_err_params)
                pg.commit()
                logger.info(u'学科编码：%d，已成功处理题目数量:%d，错误数量：%d' %(subject,count,err_count))
            except Exception as e:
                pg.rollback()
                logger.exception("学科编码：%d，批量处理-异常信息:%s" %(subject,e.message))
    finally:
        pg.close()


if __name__ == '__main__':
    findImags(11)
    # findImags(12)
