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
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support.ui import WebDriverWait
import pickle
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
html_parser = HTMLParser.HTMLParser()
logger = LoggerUtil.getLogger(__name__)


SQL_SUBJECT = 'select subject_code,subject_ename,subject_zname from t_subject'

class JyeooEkGrade:
    '''根据章节爬取题目'''
    def __init__(self,features='lxml',browserType=1):
        '''features BeautifulSoup 解析的方式:html.parser,lxml,lxml-xml,xml
            browserType:浏览器类型 1-chrome 2-Firefox
        '''
        self.session = requests.Session()
        self.maxPage = 3
        self.features = features
        self.browserType = browserType
        if browserType == 2:
            self.driver = webdriver.Firefox()
        else:
            self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.insert_sql = u'INSERT INTO  t_ques_jyeoo_20180601(qid,answer,analyses,cate,cate_name,content,options,sections,points,subject,difficulty,dg,old_id) ' \
                          'VALUES (uuid_generate_v5(uuid_ns_url(), %s),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        self.insert_sql_section = u'INSERT INTO t_last_section_20180601(section_id,title,status) VALUES (%s,%s,%s)'
        self.select_sql = u'SELECT qid,sections FROM t_ques_jyeoo_20180601 WHERE old_id=%s'
        self.select_sql_seciton = u'SELECT section_id,title FROM t_last_section_20180601 WHERE  section_id=%s and status = %s'
        self.update_sql_secs = u"UPDATE t_ques_jyeoo_20180601  SET  sections=%s  WHERE  qid=%s "
        self.cate = 1
        self.cate_name = '单选题'

    def login(self,driver):
        '''用户登录'''
        cookies = None
        last_time = 0.0
        try:
            cookies = pickle.load(open("cookies.pkl", "rb"))
            last_time = pickle.load(open("time.pkl", "rb"))
        except Exception as e:
            pass
        #8小时内 不用登陆
        if cookies and (time.time() - last_time) < 60 * 60 * 8:
            for cookie in cookies:
                driver.add_cookie(cookie)
        else:
            isLog = raw_input(u'若用户已完成登录，请输入“1”：')
            while isLog != '1':
                isLog = raw_input(u'请再次，若用户已完成登录，请输入“1”：')
            logger.info(u'用户确认已登录')

    def mainSelection(self,course,pg):
        # mongo = MongoDB()
        # coll = mongo.getCollection(COLL.SELECTION)
        driver = self.driver
        s_main_url = URL.S_MAIN_URL % course[1]
        logger.info(u'科目：%s,url:%s',course[2],s_main_url)
        driver.get(URL.ROOT_URL)
        #登录
        self.login(driver)
        try:
            driver.get(s_main_url)
            driver.implicitly_wait(10)
            driver.find_element_by_xpath(u"//table[@class='degree']//tr/td/ul/li/a[contains(.,'选择题')]").click()
            # driver.implicitly_wait(10)
            bt_driver = driver.find_element_by_id('JYE_BOOK_TREE_HOLDER')
            bt_soup = BeautifulSoup(bt_driver.get_attribute('outerHTML'),self.features)
            for ek_soup in bt_soup.find_all('li',attrs={'ek':True}):
                ek_id = ek_soup['ek']
                ek_name = ek_soup['nm']
                for bk_soup in ek_soup.find_all('li',attrs={'bk':True}):
                    grade_id = bk_soup['bk']
                    grade_name = bk_soup['nm']
                    logger.info(u'选择版本年级%s-%s-%s-%s',ek_id,ek_name,grade_id,grade_name)
                    select_sql = 'select grade_id from t_grade_ek_20180601 WHERE grade_id=%s  '
                    r = pg.getOne(select_sql,(grade_id,))
                    if r : continue
                    insert_sql = 'insert into t_grade_ek_20180601(grade_id,grade_name,ek_id,ek_name,subject_id,subject_name) ' \
                          'VALUES (%s,%s,%s,%s,%s,%s)'
                    try:
                        pg.execute(insert_sql,(grade_id,grade_name,ek_id,ek_name,course[0],course[2]))
                        pg.commit()
                    except  Exception as e:
                        pg.rollback()
                        logger.exception(u'保存年级版本ID异常，异常信息%s',e.message)
        finally:
            pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
            pickle.dump(time.time(),open("time.pkl", "wb"))


if __name__ == '__main__':
    selection = JyeooEkGrade(browserType=2)
    pg = PostgreSql()
    try:
        c_list = pg.getAll(SQL_SUBJECT)
        for course in c_list:
            selection.mainSelection(course,pg)
    finally:
        pg.close()
