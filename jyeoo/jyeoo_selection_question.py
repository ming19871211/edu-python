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

driver = None
SQL_SUBJECT = 'select subject_code,subject_ename,subject_zname from t_subject'
MAX_PAGE=3
class JyeooSelectionQuestion:
    '''根据章节爬取题目'''
    def __init__(self,features='lxml'):
        '''features BeautifulSoup 解析的方式:html.parser,lxml,lxml-xml,xml'''
        self.session = requests.Session()
        self.maxPage = 3
        self.features = features
    def mainSelection(self,course):
        # mongo = MongoDB()
        # coll = mongo.getCollection(COLL.SELECTION)

        s_main_url = URL.S_MAIN_URL % course[1]
        logger.info(u'科目：%s,url:%s',course[2],s_main_url)
        driver.get(URL.ROOT_URL)
        #登录问题
        cookies = None
        last_time = 0.0
        try:
            cookies = pickle.load(open("cookies.pkl", "rb"))
            last_time = pickle.load(open("time.pkl", "rb"))
        except Exception as e:
            pass
        if cookies and (time.time()-last_time) < 60*30:
            for cookie in cookies:
                driver.add_cookie(cookie)
        else:
            isLog = raw_input(u'若用户已完成登录，请输入“1”：')
            while isLog != '1':
                isLog=raw_input(u'请再次，若用户已完成登录，请输入“1”：')
            logger.info(u'用户确认已登录')
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
                # 点击选择教材版本
                driver.implicitly_wait(10)
                WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath("//div[@class='tree-head']").is_displayed())
                time.sleep(1)
                th_ele = driver.find_element_by_xpath("//div[@class='tree-head']")
                webdriver.ActionChains(driver).move_to_element(th_ele).perform()
                th_ele.click()
                WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath("//div[@class='tree-head']//a[@data-id='%s']" % ek_id).is_displayed())
                ek_ele = driver.find_element_by_xpath("//div[@class='tree-head']//a[@data-id='%s']" % ek_id)
                ek_ele.click()
                for bk_soup in ek_soup.find_all('li',attrs={'bk':True}):
                    grade_id = bk_soup['bk']
                    grade_name = bk_soup['nm']
                    #点击选择年级
                    driver.implicitly_wait(10)
                    WebDriverWait(driver, 10).until(lambda x : x.find_element_by_xpath("//div[@class='tree-head']").is_displayed())
                    time.sleep(1)
                    th_ele = driver.find_element_by_xpath("//div[@class='tree-head']")
                    webdriver.ActionChains(driver).move_to_element(th_ele).perform()
                    th_ele.click()
                    WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath("//div[@class='tree-head']//a[@data-id='%s']" % grade_id).is_displayed())
                    grade_ele = driver.find_element_by_xpath("//div[@class='tree-head']//a[@data-id='%s']" % grade_id)

                    grade_ele.click()
                    print ek_id, ek_name, grade_id, grade_name
                    # 只取treeview的HTML分析,防止页面太大 丢数据
                    tree_xpath = "//ul[@class='treeview']"
                    time.sleep(2)
                    WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(tree_xpath).is_displayed())
                    tree_html = driver.find_element_by_xpath(tree_xpath).get_attribute('outerHTML') # innerHTML为内部数据
                    ul_soup = BeautifulSoup(tree_html,self.features).find(name='ul', attrs={'class': 'treeview'})
                    self.recurSelection(ul_soup,driver)
        finally:
            pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
            pickle.dump(time.time(),open("time.pkl", "wb"))

    def recurSelection(self,ul_soup,driver,parent_Id=None,parent_name=None):
        '''按章节获取题目'''
        for li_soup in ul_soup.find_all('li',recursive=False):
            pk = li_soup.a['pk']
            pk_arr = pk.split('~')
            title = li_soup.a['title']
            child_ul_soup = li_soup.find('ul')
            if child_ul_soup:
                if 'expandable' in li_soup['class']:
                    div_ele = driver.find_element_by_xpath(u"//li/a[@pk='%s'][@title='%s']/../div" % (pk, title))
                    div_ele.click()
                self.recurSelection(child_ul_soup,driver,pk_arr[-2],title)
            else:
                a = driver.find_element_by_xpath(u"//li/a[@pk='%s'][@title='%s']" % (pk,title))
                selection_id = pk_arr[-2]
                selection_name = title
                if pk_arr[-1]:
                    selection_id = parent_Id
                    selection_name = parent_name
                #可以判断一下此次是否下载完成,需要实现
                # TODO
                selections = []
                selections.append({'code':selection_id,'name':selection_name})
                selections = json.dumps(selections,ensure_ascii=False)
                a.click()
                # 分析题干页面
                self.parseQuestionPg(driver,selections)

    def parseQuestionPg(self,driver,selections):
        '''分析分页题目'''
        driver.implicitly_wait(10)
        time.sleep(2)
        # root_soup = BeautifulSoup(driver.page_source, self.features)
        # div_soup = root_soup.find(name='div',attrs={'id':'pageArea'})
        # 防止加载页面太大丢数据
        pageArea_html = driver.find_element_by_id('pageArea').get_attribute('outerHTML')
        div_soup = BeautifulSoup(pageArea_html, self.features)
        #分析分页页面题目
        for li in div_soup.find_all(name='li',attrs={'class':'QUES_LI'}):
            pt1 = unicode(li.find('div',attrs={'class':'pt1'}))
            old_id = li.fieldset['id']
            content = re.findall(u'^<div\s+class=[\'"]pt1[\'"]>\s*<!--B\d+-->\s*.*?<span\s+class=[\'"]qseq[\'"]>[1-9]\d*．</span>(<a\s+href=.+?>)?(（.+?）)(</a>)?(.+?)<!--E\d+-->\s*</div>$',pt1)[0][-1]
            options=[]
            for td in li.find_all('td',attrs={'class':'selectoption'}):
                try:
                    option = td.label.get_text()
                    option = re.findall(u'^[A-Z]．(.+)$',option)[0]
                    options.append(option)
                except Exception as e:
                    pass
            options = json.dumps(options,ensure_ascii=False)
            dg = re.findall(u'<span>\s*难度：([\d\.]+?)\s*</span>',unicode(li.find('div',attrs={'class':'fieldtip-left'})))[0]
            print(pt1)
            print old_id
            print content
            print options
            print selections
            print dg
            #获取解析
            analyze_xpath = "//fieldset[@id='%s']/../div[@class='fieldtip']//i[@class='icon i-analyze']/.." % old_id
            WebDriverWait(driver, 20).until(lambda x: x.find_element_by_xpath(analyze_xpath).is_displayed())
            analyze_ele = driver.find_element_by_xpath(analyze_xpath)
            time.sleep(1)
            # driver.execute(Command.MOVE_TO, analyze_ele.location_once_scrolled_into_view)
            webdriver.ActionChains(driver).move_to_element(analyze_ele).perform()
            analyze_ele.click()
            answer, analysis, points =self.getAnswerAndAnalysis(driver)
            print answer
            print analysis
            print points


        #下一页
        opt_soup = div_soup.find('div',attrs={'class':'page'}).find('option',attrs={'selected':True})
        pages =re.findall('^\s*(\d+?)\s*/\s*(\d+?)\s*$',opt_soup.get_text())[0]
        cur_page = int(pages[0])
        total_pag = int(pages[1])
        # 当前页小于总分页数，并且小于最大允许分页
        if cur_page < total_pag and  cur_page < self.maxPage:
            next_ele = driver.find_element_by_xpath(u"//div[@id='pageArea']/div[@class='page']/div[@class='pagertips']/a[@class='next'][@title='下一页']")
            webdriver.ActionChains(driver).move_to_element(next_ele).perform()
            # driver.execute(Command.MOVE_TO, next_ele.location_once_scrolled_into_view)
            js_goPage = next_ele.get_attribute('href').replace('javascript:','')
            print next_ele.text,js_goPage
            # time.sleep(3)
            #可以调用界面点击或者直接调用函数
            # next_ele.click()
            driver.execute_script(js_goPage)
            self.parseQuestionPg(driver,selections)

    def getAnswerAndAnalysis(self,driver):
        WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath("//div[@class='box-wrapper']").is_displayed())
        time.sleep(1)
        box_wra_elel = driver.find_element_by_xpath("//div[@class='box-wrapper']")
        # with open('text.txt','w') as f: f.write(box_wra_elel.get_attribute('outerHTML'))
        box_soup = BeautifulSoup(box_wra_elel.get_attribute('outerHTML'),self.features)
        hclose_ele = box_wra_elel.find_element_by_xpath(u"//input[@title='关闭']")
        # print box_soup.find('input',attrs={'checked':'checked'},class_="radio s")
        labe_soup = box_soup.find('input', attrs={'checked': 'checked'}, class_="radio s").find_parent()
        answer = re.findall(u'^([A-Z])．.+$',labe_soup.get_text())
        answer = json.dumps(answer,ensure_ascii=False)
        #解析知识点
        point_soup = box_soup.find('em',text=u'【考点】')
        points = []
        for a_soup in point_soup.find_next_siblings('a'):
            know_name = a_soup.get_text()
            know_id = re.findall(u"openPointCard\(\s*'[a-zA-Z\d]+?'\s*,\s*'([a-zA-Z\d]+?)'\s*\);\s*return\s*false;\s*",a_soup['onclick'])[0]
            points.append({'code':know_id,'name':know_name})
        points = json.dumps(points,ensure_ascii=False)
        analysis_soup = box_soup.find('em',text=u'【分析】').parent
        analysis = re.findall(u'<div\s+class="pt[\d]"\s*>\s*<!--B[\d]-->\s*(.+?)<!--E[\d]-->\s*</div>',unicode(analysis_soup))[0].replace(u'<em>【分析】</em>','')
        #关闭解析
        hclose_ele.click()
        return (answer,analysis,points)

if __name__ == '__main__':
    # driver = webdriver.Chrome()
    driver = webdriver.Firefox()
    driver.maximize_window()
    selection = JyeooSelectionQuestion()
    pg = PostgreSql()
    try:
        c_list = pg.getAll(SQL_SUBJECT)
    finally:
        pg.close()
    for course in c_list:
        if course[0] == 20:
            selection.mainSelection(course)
