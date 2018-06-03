#!/usr/bin/python
#-*-coding:utf-8-*-

import requests
import HTMLParser
import re
import time
import json
from bs4 import BeautifulSoup #lxml解析器
from utils import LoggerUtil
from utils.SqlUtil import PostgreSql,MongoDB
from cfg import COLL,URL
from selenium import webdriver
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
html_parser = HTMLParser.HTMLParser()
logger = LoggerUtil.getLogger(__name__)

driver = None
SQL_SUBJECT = 'select subject_code,subject_ename,subject_zname from t_subject'

class JyeooSelectionQuestion:
    '''根据章节爬取题目'''
    def __init__(self):
        self.session = requests.Session()
    def mainSelection(self,course):
        # mongo = MongoDB()
        # coll = mongo.getCollection(COLL.SELECTION)

        s_main_url = URL.S_MAIN_URL % course[1]
        logger.info(u'科目：%s,url:%s',course[2],s_main_url)
        driver.get(URL.ROOT_URL)

        # isLog = raw_input(u'确认用户是否登录,1-已登陆')
        # while isLog != '1':
        #     isLog=raw_input(u'请再次确认用户是否登录,1已登陆')
        # logger.info(u'用户确认已登录')
        driver.get(s_main_url)
        driver.implicitly_wait(10)
        driver.find_element_by_xpath(u"//table[@class='degree']//tr/td/ul/li/a[contains(.,'选择题')]").click()
        root_soup = BeautifulSoup(driver.page_source, "lxml-xml")
        ul_soup=root_soup.find(name='ul',attrs={'class':'treeview'})
        self.recurSelection(ul_soup,driver)

    def recurSelection(self,ul_soup,driver):
        for li_soup in ul_soup.find_all('li',recursive=False):
            pk = li_soup.a['pk']
            title = li_soup.a['title']
            child_ul_soup = li_soup.find('ul')
            if child_ul_soup:
                if 'expandable' in li_soup['class']:
                    div_ele = driver.find_element_by_xpath(u"//li/a[@pk='%s'][@title='%s']/../div" % (pk, title))
                    div_ele.click()
                self.recurSelection(child_ul_soup,driver)
            else:
                a = driver.find_element_by_xpath(u"//li/a[@pk='%s'][@title='%s']" % (pk,title))
                #可以判断一下此次是否下载完成
                a.click()
                # 分析题干页面
                self.parseQuestionPg(driver)

    def parseQuestionPg(self,driver):
        driver.implicitly_wait(10)
        time.sleep(3)
        root_soup = BeautifulSoup(driver.page_source, "lxml-xml") # html.parser
        div_soup = root_soup.find(name='div',attrs={'id':'pageArea'})
        #分析分页页面题目
        for li in div_soup.find_all(name='li',attrs={'class':'QUES_LI'}):
            pt1 = unicode(li.find('div',attrs={'class':'pt1'}))
            content = re.findall(u'^<div\s+class=[\'"]pt1[\'"]>\s*<!--B1-->\s*<span\s+class=[\'"]qseq[\'"]>[1-9]\d*．</span>(<a\s+href=.+?>)?(（.+?）)(</a>)?(.+?)</div>$',pt1)[0][-1]
            options=[]
            for td in li.find_all('td',attrs={'class':'selectoption'}):
                try:
                    option = td.label.get_text()
                    option = re.findall(u'^[A-Z]．(.+)$',option)[0]
                    options.append(option)
                except Exception as e:
                    pass
            options = json.dumps(options,ensure_ascii=False)
            print(pt1)
            print content
            print options
        #下一页
        select_soup = div_soup.find('select',attrs={'onchange':'goPage(this.value,this)'})
        print(select_soup)

if __name__ == '__main__':
    driver = webdriver.Chrome()
    selection = JyeooSelectionQuestion()
    pg = PostgreSql()
    try:
        c_list = pg.getAll(SQL_SUBJECT)
    finally:
        pg.close()
    for course in c_list:
        if course[0] == 20:
            selection.mainSelection(course)
