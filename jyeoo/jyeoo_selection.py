#!/usr/bin/python
#-*-coding:utf-8-*-

import requests
import random
import HTMLParser
from bs4 import BeautifulSoup #lxml解析器
from utils import LoggerUtil
from utils.SqlUtil import PostgreSql,MongoDB
from cfg import COLL,URL
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
html_parser = HTMLParser.HTMLParser()

logger = LoggerUtil.getLogger(__name__)
SQL_SUBJECT = 'select subject_code,subject_ename,subject_zname from t_subject'
SEQ = 1
class JyeooSelection:
    def __init__(self):
        self.session = requests.Session()
    def mainSelection(self,c_url,category_url,course):
        c_name = course[1]
        c_url = c_url % c_name
        category_url = category_url % c_name
        response = self.session.get(c_url)
        root_soup = BeautifulSoup(html_parser.unescape(response.content), "lxml")
        ul_soup = root_soup.find('ul',id='JYE_BOOK_TREE_HOLDER')
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.SELECTION)
        for ek_li_soup in ul_soup.find_all('li',attrs={'ek':True}):
            #教材ID，教材名称
            ek_id = ek_li_soup['ek']
            ek_name = ek_li_soup['nm']
            for bk_li_soup in ek_li_soup.find_all('li',attrs={'bk':True}):
                # 年级ID，年级名称
                bk_id = bk_li_soup['bk']
                bk_name = bk_li_soup['nm']
                data = {'a':bk_id,'q':'','f':0,'cb':'_setQ','r':random.random()}
                resp = self.session.post(category_url,data=data)
                pk_ul_soup = BeautifulSoup(html_parser.unescape(resp.content), "lxml").find('ul',id='JYE_POINT_TREE_HOLDER')
                try:
                    s_rows = self.pareSelection(pk_ul_soup,bk_id,bk_name,ek_id,ek_name,course,1)
                    coll.insert_many(s_rows)
                    logger.info(u'完成下载菁优章节，教材名称：%s，年级名称：%s，科目名称：%s-%s，科目主url：%s',ek_name,bk_name,c_name,course[-1],c_url)
                except  Exception as e:
                    logger.exception(u'分析下载菁优章节异常，教材名称：%s，年级名称：%s，科目名称：%s-%s，科目主url：%s',ek_name,bk_name,course[-1],c_name,c_url)

    def pareSelection(self,ul_soup,bk_id,bk_name,ek_id,ek_name,course,level,parent_id=None):
        '''bk：年级，ek: 教材，level：级别，parent_id：上级章节ID'''
        global SEQ
        rows = []
        for li in  ul_soup.find_all('li',attrs={'pk':True},recursive=False):
            pk_q = li['pk']
            pk_arr = pk_q.split('~')
            pk_id = pk_arr[-1]
            pk_name = li['nm']
            type_id = 1 #章节
            type_name = u'章节'
            if pk_id:
                pk_name = pk_name.replace(pk_id+'：','').strip()
                type_id = 2
                type_name = u'知识点'
            else:
                pk_id = pk_arr[-2]
            row = {'type_id':type_id,'type_name':type_name,'ek_id':ek_id,'ek_name':ek_name,'grade_id':bk_id,'grade_name':bk_name,
                   'level':level,'parent_select_id':parent_id,'pk_q':pk_q,'pk_id':pk_id,'pk_name':pk_name,'seq':SEQ,
                   'c_id':course[0],'c_name':course[1],'c_zname':course[2]}
            rows.append(row)
            SEQ += 1
            child_ul_soup = li.find('ul')
            if child_ul_soup:
                rows.extend(self.pareSelection(child_ul_soup,bk_id,bk_name,ek_id,ek_name,course,level+1,pk_id))
            else:
                row['isLast'] = True
        return rows


if __name__ == '__main__':
    selection = JyeooSelection()
    pg = PostgreSql()
    try:
        c_list = pg.getAll(SQL_SUBJECT)
    finally:
        pg.close()
    for course in c_list:
        #pass
        selection.mainSelection(URL.C_URL, URL.CATEGORY_URL,course)
