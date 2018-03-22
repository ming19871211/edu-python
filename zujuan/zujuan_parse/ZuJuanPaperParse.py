#!/usr/bin/python
#-*-coding:utf-8-*-


import requests
import HTMLParser #处理html编码字符
import re
import json
from utils import LoggerUtil
from utils.SqlUtil import MongoDB
import pymongo
import urlparse
from bs4 import BeautifulSoup #lxml解析器
from cfg import subjects,xds,PATH,URL,COLL
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

html_parser = HTMLParser.HTMLParser()
logger = LoggerUtil.getLogger(__name__)
logger_major = LoggerUtil.getLogger('major')




class PaperParse:
    '''分析组卷网的试卷页面'''

    def __init__(self, url=URL.rootUrl):
        self.session = requests.Session()
        self.session.get(url)

    def parseParperPropAll(self,url=URL.paper_url):
        '''分析试卷的所有公共属性'''
        mongo = MongoDB()
        #创建唯一索引
        # for key, value in COLL.type.items():
        #     coll = mongo.getCollection(value)
        #     coll.create_index([(key+'_id',pymongo.ASCENDING)],unique=True)
        for key, value in subjects.items():
            for xd in value['xds']:
                    self.parsePaperProp(value,xd,mongo,url)

    def parsePaperProp(self,subject,xd,mongo,url=URL.paper_url):
        subjectCode = xd*10+subject['code']
        paper_url = url % (subject['chid'],xd)
        response = self.session.get(paper_url)
        root_soup = BeautifulSoup(html_parser.unescape(response.content),"lxml")
        count_ignore = 0
        for type_soup in root_soup.find_all('div',attrs={'class':'type-items'}):
            type_name = type_soup.find('div',attrs={'class':'type-tit'}).get_text().replace('：','').strip()
            if type_name == u'版本':
                key = 'version'
            elif type_name == u'年级':
                key = 'grade'
            elif type_name == u'类型':
                key = 'papertype'
            elif type_name == u'地区':
                key = 'province'
            coll = mongo.getCollection(COLL.type[key])
            column_id = key + '_id'
            column_name = key + '_name'
            for a in type_soup.find_all('a'):
                item_id= re.findall('xd.+&.+?=(.*?)$', a['href'])[0]
                item_name = a.get_text()
                if item_id:
                    doc = coll.find_one({column_id:item_id})
                    if doc:
                        if doc[column_name] == item_name:
                            cids = doc['cids']
                            if subjectCode in cids:
                                count_ignore += 1
                                continue
                            else:
                                cids.append(subjectCode)
                                coll.update_one({column_id:item_id},{'$set':{'cids':cids}})
                        else:
                            raise ValueError(u'试卷类型属性出现了id与name不对应情况 id：%s,name1：%s,name2：%s,课程id：%d' %(item_id,item_name,doc[column_name],subjectCode))
                    else:
                        coll.insert_one({column_id:item_id,column_name:item_name,'cids':[subjectCode]})
        logger.info(u'完成处理学科：%s，学段：%d，学科编码：%d，忽略类型：%d',subject['name'],xd,subjectCode,count_ignore)


    def downloadPaperIds(self,subject,xd,paper_pg_url=URL.paper_pg_url,baseUrl=URL.rootUrl):
        subjectCode = xd * 10 + subject['code']
        mongo = MongoDB()
        coll_grade = mongo.getCollection(COLL.type['grade'])
        coll_province = mongo.getCollection(COLL.type['province'])
        cursor_grade = coll_grade.find({'cids':{'$all':[subjectCode]}})
        cursor_province = coll_province.find({'cids':{'$all':[subjectCode]}})
        #将省份迭代器转换为tuple
        provinces = tuple(cursor_province)
        #学科试卷类型字典
        papertype_dic = {}
        for doc_papertype in mongo.getCollection(COLL.type['papertype']).find({'cids':{'$all':[subjectCode]}}):
            papertype_dic[doc_papertype['papertype_name']]  = doc_papertype['papertype_id']
        #试卷数据集合
        coll_paper = mongo.getCollection(COLL.paper)
        coll_paper.create_index([('paper_id',pymongo.ASCENDING)],unique=True)
        pg = 1
        for doc_grade in cursor_grade:
            for doc_province in provinces:
                url = paper_pg_url % (subject['chid'], xd, pg, doc_grade['grade_id'], doc_province['province_id'])
                try:
                    self.downloadPaperPgIds(url,subjectCode,papertype_dic,doc_grade,doc_province,coll_paper,baseUrl)
                    logger.info(u'完成学科名称%s,学科编码%d，年级:%s，地区:%s，所有试卷Id等简单信息爬取',
                                subject['name'],subjectCode,doc_grade['grade_name'],doc_province['province_name'])
                except Exception as e:
                    logger.exception(u'下载试卷分页信息错误，学科名称%s,学科编码%d，爬取url:%s,年级:%s，地区:%s 异常信息：%s',
                                     subject['name'],subjectCode,url,doc_grade['grade_name'],doc_province['province_name'],e.message)

    def downloadPaperPgIds(self,url,subjectCode,papertype_dic,doc_grade,doc_province,coll_paper,baseUrl):
        response = self.session.get(url)
        root_soup = BeautifulSoup(html_parser.unescape(response.content), "lxml")
        div_soup = root_soup.find('div', attrs={'class': 'search-list'})
        for li in div_soup.find_all('li'):
            a_soup = li.find('div', attrs={'class': 'test-txt'}).find('a')
            paper_id = re.findall(r'/view-?(\d+?)\.s?html$', a_soup['href'])[0]
            paper_name = a_soup['title']
            doc_paper = coll_paper.find_one({'paper_id': paper_id})
            # 分析出试卷类型
            papertype_name = li.find('i', attrs={'class': 'icona-leixing'}).parent.get_text().replace(u'类型：','').strip()
            papertype_id = papertype_dic[papertype_name]
            # 合成试卷详情url
            paper_url = urlparse.urljoin(baseUrl, a_soup['href'])
            if doc_paper:
                if doc_paper['cid'] != subjectCode:
                    raise ValueError(u'试卷学科编程异常id:%s，%d-%d' % (paper_id, doc_paper['cid'], subjectCode))
                if doc_paper['url'] != paper_url:
                    raise ValueError(u'试卷url异常id:%s，%s-%s' % (paper_id, doc_paper['url'], paper_url))
                # 更新 属性 （类型、年级、地址）
                prop_dic = {}
                if not papertype_id in doc_paper['papertypes']:
                    papertypes = doc_paper['papertypes']
                    papertypes.append(papertype_id)
                    prop_dic['papertypes'] = papertypes
                if not doc_grade['grade_id'] in doc_paper['grades']:
                    grades = doc_paper['grades']
                    grades.append(doc_grade['grade_id'])
                    prop_dic['grades'] = grades
                if not doc_province['province_id'] in doc_paper['provinces']:
                    provinces = doc_paper['provinces']
                    provinces.append(doc_province['province_id'])
                    prop_dic['provinces'] = provinces
                if prop_dic:
                    coll_paper.update_one({'paper_id': paper_id}, {'$set': prop_dic})
            else:
                doc_paper = {'paper_id': paper_id, 'paper_name': paper_name, 'url': paper_url, 'cid': subjectCode,
                             'papertypes': [papertype_id],
                             'grades': [doc_grade['grade_id']],
                             'provinces': [doc_province['province_id']]}
                coll_paper.insert_one(doc_paper)
        # 分页下载试卷Id
        pagenum_div = root_soup.find('div',attrs={'class':'pagenum'})
        if pagenum_div:
            next_soup = pagenum_div.find('a',text=re.compile(u'^\s*下一页\s*$'))
            if next_soup:
                next_url = urlparse.urljoin(baseUrl, next_soup['href'])
                try:
                    self.downloadPaperPgIds(next_url, subjectCode, papertype_dic, doc_grade, doc_province, coll_paper, baseUrl)
                except Exception as e:
                    logger.exception(u'下载试卷分页信息错误，学科编码%d，爬取url:%s,年级:%s，地区:%s 异常信息：%s',
                                     subjectCode,next_url,doc_grade['grade_name'],doc_province['province_name'],e.message)

    def downloadPaper(self,subject,xd):
        '''下载试卷'''
        subjectCode = xd * 10 + subject['code']
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.paper)
        for doc in coll.find({'cid':subjectCode,'status':{'$exists':False}}):
            try:
                response = self.session.get(doc['url'])
                #root_soup = BeautifulSoup(response.content, "lxml")
                #script_soup = root_soup.find('script',text=re.compile(u'var\s*MockDataTestPaper\s*=\s*\['))
                #datastr = re.findall(u'var\s*MockDataTestPaper\s*=\s*(\[{.+?}\])\s*;\s*',script_soup.get_text())[0]
                datastr = re.findall(u'var\s*MockDataTestPaper\s*=\s*(\[{.+?}\])\s*;\s*',response.content)[0]
                MockDataTestPaper = json.loads(datastr)
                coll.update_one({'paper_id':doc['paper_id']},
                                {"$set": {"paper_detail": MockDataTestPaper, 'status': 1},
                                 "$currentDate": {"lastModified": True}})
            except Exception as e:
                logger.exception(u'下载试卷失败，试卷Id：%s，试卷url：%s，学科名称：%s，学科编码：%d',
                                 doc['paper_id'],doc['url'],subject['name'],subjectCode)
                if  re.findall(r'sorry！\s*系统出错了！',response.content):
                    coll.update_one({'paper_id': doc['paper_id']},
                                    {"$set": {"error": u'sorry！ 系统出错了！', 'status': -1},
                                     "$currentDate": {"lastModified": True}})

if __name__ == '__main__':
    parse = PaperParse()
    #分析试卷的所有公共属性
    #parse.parseParperPropAll()
    #下载指定学科、学段的试卷Id
    #parse.downloadPaperIds(subjects['math'],3)
    #下载书卷
    #parse.downloadPaper(subjects['math'],3)
    print  u'\u7ade\u8d5b\u6d4b\u8bd5'
