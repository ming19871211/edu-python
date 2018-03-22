#!/usr/bin/python
#-*-coding:utf-8-*-

import HTMLParser #处理html编码字符
from bs4 import BeautifulSoup #lxml解析器
import requests
import os
import re
import json
import urlparse
import time
from utils import LoggerUtil
from utils.SqlUtil import MongoDB
import pymongo
from cfg import subjects,xds,PATH,URL,COLL
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

html_parser = HTMLParser.HTMLParser()

logger = LoggerUtil.getLogger(__name__)
logger_major = LoggerUtil.getLogger('major')



class ZuJuanParse:
    '''分析组卷网的主页面'''

    def __init__(self,url=URL.rootUrl):
        self.session = requests.Session()
        self.session.get(url)

    def parseQuestionAllType(self):
        '''分析题目所有类型'''
        mongo = MongoDB()
        for key, value in subjects.items():
            for xd in value['xds']:
                self.parseQuesiontAllTypeByCid(value,xd,mongo)
    def parseQuesiontAllTypeByCid(self,subject,xd,mongo,baseUrl=URL.knowledUrl):
        subjectCode = xd*10 + subject['code']
        url = baseUrl % (subject['chid'], xd)
        logger.info(u'开始分析题目所有类型--学科：%s，学段：%d，编码：%d，url:%s', subject['name'], xd, subjectCode, url)
        response = self.session.get(url)
        root_soup = BeautifulSoup(html_parser.unescape(response.content), "lxml")
        for type_soup in root_soup.find_all('div', attrs={'class': 'tag-items'}):
            # question_type_name = type_soup.find('div',attrs={'class':'tag-tit'}).get_text().strip()
            question_type_code = type_soup.find('input',attrs={'type':'hidden'})['name'].strip()
            if question_type_code == u'grade_id[]':
                coll = mongo.getCollection(COLL.question_type['grade'])
                # coll.create_index([("grade_id", pymongo.ASCENDING)], unique=True)
                for span_soup in type_soup.find_all('span',attrs={'class':'checkbox'}):
                    grade_name = span_soup.get_text(strip=True)
                    grade_id = span_soup.find('input',attrs={'type':'checkbox'})['value'].strip()
                    doc = coll.find_one({'grade_id':grade_id,'grade_name':grade_name})
                    if doc:
                        cids = doc['cids']
                        if not subjectCode in cids:
                            cids.append(subjectCode)
                            coll.update_one({'grade_id':grade_id,'grade_name':grade_name},{"$set":{"cids":cids}})
                    else:
                        coll.insert_one({'grade_id':grade_id,'grade_name':grade_name,'cids':[subjectCode]})
            else:
                if question_type_code == 'kid_num' : continue
                coll = mongo.getCollection(COLL.question_type[question_type_code])
                # coll.create_index([("id", pymongo.ASCENDING)], unique=True)
                for a_soup in  type_soup.find_all('a',attrs={'data-name':True}):
                    data_title = a_soup.get_text(strip=True)
                    data_value = a_soup['data-value']
                    if not data_value : continue
                    # data_name = a_soup['data-name']
                    doc = coll.find_one({'id': data_value,'name':data_title})
                    if doc:
                        cids = doc['cids']
                        if not subjectCode in cids:
                            cids.append(subjectCode)
                            coll.update_one({'id': doc['id'],'name':data_title}, {"$set": {"cids": cids}})
                    else:
                        coll.insert_one({'id': data_value, 'name': data_title, 'cids': [subjectCode]})

    def mainKnowled(self):
        '''分析所有学科的知识点'''
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.knowled)
        #coll.create_index([("id",pymongo.ASCENDING)],unique=True)
        for key, value in subjects.items():
            for xdKey,xdValue in xds.items():
                if xdValue['xd'] in value['xds']:
                    try:
                        coll.insert(self.parseKnowled(value, xdValue))
                    except Exception as e:
                        logger.exception(u'处理学科：%s,学段：%s；出现异常，异常信息：%s',value['name'],xdValue['name'],e.message)

    def parseKnowled(self, subject, xd_dic, baseUrl=URL.knowledUrl, rootPath=PATH.rootPath, jsonUrl=URL.knowledJsonUrl,hostUrl=URL.rootUrl):
        '''按知识点分析'''
        if not xd_dic['xd'] in subject['xds']:
            logger.error(u'学段有误；学科：%s，学段：%s，不存在',subject['name'],xd_dic['name'])
            return
        url = baseUrl % (subject['chid'], xd_dic['xd'])
        subjectCode = xd_dic['xd']*10 + subject['code']
        logger.info(u'开始分析知识点--学科：%s，学段：%s，编码：%d，url:%s',subject['name'],xd_dic['name'],subjectCode,url)
        #文件名称命名原则是 学科编码-学科名称-学段编码.html
        file_name = os.path.join(rootPath,'%d-%s-%d'%(subject['chid'],subject['name'],xd_dic['xd']))
        if os.path.exists(file_name+".html") and os.path.exists(file_name+".json"):
            with open(file_name + '.html', 'r') as file:html_text = file.read()
            with open(file_name + '.json', 'r') as f: knowleds_json=json.loads(f.read())
        else:
            html_text = self.session.get(url).content
            with open(file_name+'.html','w') as file:file.write(html_text)
            headers = {"Host": urlparse.urlparse(hostUrl).netloc, "Referer": url, }
            knowledjsonUrl = jsonUrl %('0',int(time.time()*1000))
            print knowledjsonUrl
            response = self.session.get(knowledjsonUrl, headers=headers)
            with open(file_name + '.json', 'w') as f: f.write(response.content)
            knowleds_json = response.json()
        #分析内容
        # root_soup = BeautifulSoup(html_parser.unescape(html_text), "lxml")
        # for a in root_soup.find('div',attrs={'id':'J_Tree'}).find_all('a'):
        #     knowled_id = re.findall(u"knowledges=(.+?)&", a['href'])[0]
        #     knowled_name = a.get_text()
        #     print knowled_id,knowled_name

        #根据json数据下载子数据
        knowleds= []
        for knowled in knowleds_json:
            knowleds.append({'id':knowled['id'],'title':knowled.get('title'),'parentId':None,
                             'level':1,'cid':subjectCode,'hasChild':knowled['hasChild']})
            if knowled['hasChild']:
                knowleds.extend(self.downloadParseKnowledsJson(knowled['id'],subjectCode,2,jsonUrl))
        logger.info(u'结束分析知识点--学科：%s，学段：%s，编码：%d，url:%s', subject['name'], xd_dic['name'], subjectCode, url)
        return knowleds

    def downloadParseKnowledsJson(self,parentKnowledId,subjectCode,level,jsonUrl=URL.knowledJsonUrl):
        knowleds = []
        knowledjsonUrl = jsonUrl % (parentKnowledId, int(time.time() * 1000))
        response = self.session.get(knowledjsonUrl)
        for knowled in response.json():
            knowleds.append({'id': knowled['id'], 'title':knowled.get('title'), 'parentId': parentKnowledId,
                             'level':level,'cid': subjectCode, 'hasChild': knowled['hasChild']})
            #print knowled['id'], knowled.get('title'),parentKnowledId,subjectCode,knowled['hasChild']
            if knowled['hasChild']:
                knowleds.extend(self.downloadParseKnowledsJson(knowled['id'],subjectCode,level+1,jsonUrl))
        return knowleds

    def updteTotalKnowled(self):
        '''给知识点增加题目总数total字段'''
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.knowled)
        for key, value in subjects.items():
            for xd in value['xds']:
                self.updteTotalKnowledByCid(value,xd,coll)

    def updteTotalKnowledToSubject(self,subject,xd):
        '''更新指定学科学段的total字段'''
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.knowled)
        self.updteTotalKnowledByCid(subject, xd, coll)

    def updteTotalKnowledByCid(self,subject,xd,coll,knowledUrl=URL.knowledUrl,grade=URL.grade,questionBatchUrl= URL.questionBatchUrl):
        '''根据学科课程更新知识点的total字段'''
        subjectCode = xd * 10 + subject['code']
        logger.info(u'开始设置知识点题目数量--学科：%s，学段编码：%s，编码：%d', subject['name'], xd, subjectCode)
        knowledUrl = knowledUrl % (subject['chid'], xd)
        #必须先请求一下页面
        self.session.get(knowledUrl)
        cursor = coll.find({'cid':subjectCode})
        for doc in cursor:
            questionsUrl = questionBatchUrl %(doc['id'],grade[xd],1,time.time()*1000)
            try:
                rs = self.session.get(questionsUrl).json()
                if doc.has_key('total') and doc['total'] == rs['total']: continue
                #print rs,questionsUrl
                coll.update_one({'id':doc['id']},{"$set":{"total":rs['total']},"$currentDate": {"lastModified": True}})
            except Exception as e:
                logger.exception(u'处理学科：%s,学科编码：%d；出现异常，异常信息：%s', subject['name'], subjectCode, e.message)
        logger.info(u'结束设置知识点题目数量--学科：%s，学段编码：%s，编码：%d，更新数量%d', subject['name'], xd, subjectCode,cursor.count())


    def generateLastKnowledPgScrapyUrl(self):
        '''生成最后知识点分析爬取的url'''
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.knowled)
        coll_pg = mongo.getCollection(COLL.pg_url)
        #coll_pg.create_index([("kid", pymongo.ASCENDING),("pg", pymongo.ASCENDING)], unique=True)
        for key, value in subjects.items():
            for xd in value['xds']:
                try:
                    coll_pg.insert_many(self.generateLastKnowledPgScrapyUrlByCid(value, xd, coll))
                except Exception as e:
                    logger.exception(u'生成知识点url错误，学科：%s,学段:%d,错误信息:%s',value['name'],xd,e.message)

    def updateOrInsertLastKnowledPgScrapyUrl(self,subject,xd):
        '''修改或新增pg表中内容为最新'''
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.knowled)
        coll_pg = mongo.getCollection(COLL.pg_url)
        count_add = 0
        count_update = 0
        for kpg in self.generateLastKnowledPgScrapyUrlByCid(subject,xd,coll):
            doc = coll_pg.find_one({'kid':kpg['kid'],'pg':kpg['pg']})
            if not doc:
                coll_pg.insert_one(kpg)
                count_add += 1
            elif doc['total'] != kpg['total']:
                coll_pg.update_one({'kid':kpg['kid'],'pg':kpg['pg']},
                                   {'$set':{'total':kpg['total'],'rows':kpg['rows']},
                                    '$unset':{'status'}})
                count_update +=1
        logger.info(u'新增爬取pg数量：%d,修改爬取的pg数量:%d',count_add,count_update)

    def generateLastKnowledPgScrapyUrlByCid(self,subject,xd,coll,questionBatchUrl= URL.questionBatchUrl,
                                            grade=URL.grade,rows=10):
        subjectCode = xd * 10 + subject['code']
        logger.info(u'开始生成最后一级知识点分页爬取题目的url--学科：%s， 编码：%d',subject['name'], subjectCode)
        params = []
        cursor = coll.find({'cid': subjectCode,'hasChild':False})
        grade_params = grade[xd]
        for doc in cursor:
            total = doc['total']
            count_pg = total/rows+1
            r = total % rows
            for pg in range(1,count_pg):
                params.append(self.getUrl(doc,grade_params,pg,rows,subjectCode,questionBatchUrl))
            if r :
                params.append(self.getUrl(doc,grade_params,count_pg,r,subjectCode,questionBatchUrl))
        logger.info(u'完成生成最后一级知识点分页爬取题目的url--学科：%s， 编码：%d', subject['name'], subjectCode)
        return params

    def getUrl(self,doc,grade_params,pg,rows,subjectCode,questionBatchUrl):
        questionsUrl = questionBatchUrl % (doc['id'],grade_params, pg, time.time() * 1000)
        return {'url':questionsUrl,'kid':doc['id'],'ktitle':doc['title'],'level':doc['level'],
                'pg':pg,'rows':rows,'total':doc['total'],'cid':subjectCode}

    def localDataToRemote(self):
        '''数据库之前复制数据'''
        mongo_local = MongoDB()
        mongo_remote = MongoDB('192.168.26.159',27017)
        cursor = mongo_local.getCollection(COLL.pg_url).find({'status':1})
        coll_remote = mongo_remote.getCollection(COLL.pg_url)
        for doc in cursor:
            coll_remote.update_one({'kid':doc['kid'],'pg':doc['pg']},{"$set":{'status':doc['status'],'pgdata':doc['pgdata']}})


    def generateQuestions(self,subjectCode):
        mongo = MongoDB()
        coll_question = mongo.getCollection(COLL.question)
        # coll_question.create_index([("question_id", pymongo.ASCENDING)], unique=True)
        cursor = mongo.getCollection(COLL.pg_url).find({'cid':subjectCode,'status':1})
        count_add = 0
        count_update = 0
        count_repeat = 0
        for doc in cursor:
            kid =  doc['kid']
            ktitle = doc['ktitle']
            for question in doc['pgdata']['data'][0]['questions']:
                q = coll_question.find_one({'question_id':question['question_id']})
                if q:
                    kids = q['kids']
                    flag = False
                    for kid_dic in kids:
                        if kid_dic['kid'] == kid:
                            flag = True
                            count_repeat += 1
                            break
                    if flag:continue
                    kids.append({'kid':kid,'ktitle':ktitle})
                    coll_question.update_one({'question_id':question['question_id']},
                                             {'$set':{'kids':kids}})
                    count_update += 1
                else:
                    data = {'question_id':question['question_id'],'cid':subjectCode,
                            'old_data':question,'kids':[{'kid':kid,'ktitle':ktitle}]}
                    coll_question.insert_one(data)
                    count_add += 1
        logger.info(u'本次生成学科：%d，新增题目：%d,修改kids数量：%d,忽略掉的重复题目:%d',subjectCode,count_add,count_update,count_repeat)


if __name__ == '__main__':
    parse= ZuJuanParse()
    #分析所有题目的类型
    #parse.parseQuestionAllType()
    #下载知识点关系表
    #parse.mainKnowled()
    #给知识点增加题目数量字段
    #parse.updteTotalKnowled()
    #生成最后知识点分析爬取的url
    #parse.generateLastKnowledPgScrapyUrl()
    #用于数据库之前复制数据
    #parse.localDataToRemote()
    #生成爬取的题目
    #parse.generateQuestions(23)
    flag = -1 # 1-修改total，2-生成爬取的题目 -1-不执行
    if flag == 1:
        subject = subjects['math']
        xd = 2
        parse.updteTotalKnowledToSubject(subject,xd)
        parse.updateOrInsertLastKnowledPgScrapyUrl(subject,xd)
    elif flag == 2:
        subject_Code = 20
        parse.generateQuestions(subject_Code)














