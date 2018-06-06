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
SQL_SUBJECT_DOWLOAD = 'SELECT subject_id FROM t_grade_ek_20180601 WHERE  status = 1 GROUP BY subject_id'
MAX_PAGE=3
#默认设置的最大一次爬取数量
MAX_QUES_COUNT = 150
NO_QUES_MESS=u'对不起，当前条件下没有试题，菁优网正在加速解析试题，敬请期待！'

class JyeooSelectionQuestion:
    '''根据章节爬取题目'''
    def __init__(self,features='lxml',browserType=1,max_ques_count=MAX_QUES_COUNT):
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
        self.question_count = 0
        #最大爬题数量
        self.question_Max_count = max_ques_count

    def login(self,driver):
        '''用户登录'''
        cookies = None
        last_time = 0.0
        try:
            cookies = pickle.load(open("cookies.pkl", "rb"))
            last_time = pickle.load(open("time.pkl", "rb"))
        except Exception as e:
            pass
        #2小时内 不用登陆
        if cookies and (time.time() - last_time) < 60 * 60 * 4:
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
            # driver.find_element_by_xpath(u"//table[@class='degree']//tr/td/ul/li/a[contains(.,'选择题')]").click()
            driver.find_element_by_xpath(u"//table[@class='degree']//tr/td/ul/li/a[@onclick=\"_setPageData(this,'ct','1')\"]").click()
            # driver.implicitly_wait(10)
            bt_driver = driver.find_element_by_id('JYE_BOOK_TREE_HOLDER')
            bt_soup = BeautifulSoup(bt_driver.get_attribute('outerHTML'),self.features)
            for ek_soup in bt_soup.find_all('li',attrs={'ek':True}):
                ek_id = ek_soup['ek']
                ek_name = ek_soup['nm']
                # 判断此教材是否要下载
                select_sql_e = 'select ek_id from t_grade_ek_20180601 WHERE ek_id=%s AND subject_id=%s AND status = 1'
                r = pg.getOne(select_sql_e,(ek_id,course[0]))
                if not r : continue
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
                    # 判断此年级是否要下载
                    select_sql_g = 'select grade_id from t_grade_ek_20180601 WHERE grade_id=%s AND ek_id=%s AND subject_id=%s AND status = 1'
                    r = pg.getOne(select_sql_g, (grade_id,ek_id, course[0]))
                    if not r: continue
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
                    logger.info(u'选择版本年级%s-%s-%s-%s',ek_id,ek_name,grade_id,grade_name)
                    # 只取treeview的HTML分析,防止页面太大 丢数据
                    tree_xpath = "//ul[@class='treeview']"
                    time.sleep(2)
                    WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(tree_xpath).is_displayed())
                    tree_html = driver.find_element_by_xpath(tree_xpath).get_attribute('outerHTML') # innerHTML为内部数据
                    ul_soup = BeautifulSoup(tree_html,self.features).find(name='ul', attrs={'class': 'treeview'})
                    self.recurSelection(ul_soup,driver,course,pg)
                    update_sql_g = 'UPDATE t_grade_ek_20180601 SET status=2  WHERE grade_id=%s AND ek_id=%s AND subject_id=%s '
                    try:
                        pg.execute(update_sql_g,(grade_id,ek_id,course[0]))
                        pg.commit()
                    except Exception as e:
                        pg.rollback()
                        logger.exception(u'学科：%s，版本：%，年级：%s，下载完成标记异常', course[2], ek_name,grade_name)

        finally:
            pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
            pickle.dump(time.time(),open("time.pkl", "wb"))

    def recurSelection(self,ul_soup,driver,course,pg,parent_Id=None,parent_name=None):
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
                self.recurSelection(child_ul_soup,driver,course,pg,pk_arr[-2],title)
            else:
                a = driver.find_element_by_xpath(u"//li/a[@pk='%s'][@title='%s']" % (pk,title))
                section_id = pk_arr[-2]
                section_name = title
                if pk_arr[-1]:
                    section_id = parent_Id
                    section_name = parent_name
                #判断此次是否下载完成,完成这直接跳过
                status = 1
                r = pg.getOne(self.select_sql_seciton,(pk,status))
                if r: continue
                sections = [{'code':section_id,'name':section_name}]
                if self.browserType == 2:
                    webdriver.ActionChains(driver).move_to_element(a)
                else:
                    webdriver.ActionChains(driver).move_to_element(a).perform()
                a.click()
                # 分析题干页面
                self.parseQuestionPg(driver,sections,course,pg)
                try:
                    pg.execute(self.insert_sql_section,(pk,title,status))
                    pg.commit()
                except Exception as e:
                    pg.rollback()
                    logger.exception(u'保存last章节下载完成标记异常,pk：%s，title：%s',pk,title)

    def parseQuestionPg(self,driver,sections,course,pg):
        '''分析分页题目'''
        driver.implicitly_wait(10)
        time.sleep(3)
        #获取题目信息页面
        pageArea_html = driver.find_element_by_id('pageArea').get_attribute('outerHTML')
        div_soup = BeautifulSoup(pageArea_html, self.features)
        #判断是页面是否有题目
        if pageArea_html.find(NO_QUES_MESS) > -1:
            #没有题目
            logger.info(u'该页面没有题目，%s-%s',course[2],json.dumps(sections,ensure_ascii=False))
            return
        #分析分页页面题目
        for li in div_soup.find_all(name='li',attrs={'class':'QUES_LI'}):
            try:
                pt1 = unicode(li.find('div',attrs={'class':'pt1'}))
                old_id = li.fieldset['id']
                content_arr = re.findall(u'^<div\s+class=[\'"]pt1[\'"]>\s*<!--B\d+-->\s*(.*?)<span\s+class=[\'"]qseq[\'"]>[1-9]\d*．</span>(<a\s+href=.+?>)?(（.+?）)(</a>)?(.+?)<!--E\d+-->\s*</div>$',pt1)[0]
                content = u'%s%s'%(content_arr[0],content_arr[-1])
                # print content
                # try:
                #     sql = 'UPDATE t_ques_jyeoo_20180601 SET content=%s WHERE old_id=%s'
                #     pg.execute(sql,(content,old_id))
                #     pg.commit()
                # except Exception as ex:
                #     pg.rollback()
                #     logger.exception(u'更新题干异常：%s，old_id:%s',ex.message,old_id)

                options=[]
                for td in li.find_all('td',attrs={'class':'selectoption'}):
                    try:
                        option = unicode(td.label)
                        option = re.findall(u'^<label\s+class[="a-z\sA-Z]*>[A-Z]．(.+)</label>$',option)[0]
                        options.append(option)
                    except Exception as e0:
                        logger.error(u'加工选项异常，原始题目id：%s,选择内容：%s',old_id,unicode(td))
                        raise e0
                options = json.dumps(options,ensure_ascii=False)
                dg = re.findall(u'<span>\s*难度：([\d\.]+?)\s*</span>',unicode(li.find('div',attrs={'class':'fieldtip-left'})))[0]
                difficulty = 5 - int(float(dg) * 5)
                # 判断题目是否成在，存在就不要在下载解析了，continue
                r = pg.getOne(self.select_sql,(old_id,))
                if r:
                    qid = r[0]
                    secs = r[1]
                    #判断章节是否已添加到题目总
                    isNotExists = True
                    for sec in secs:
                        if sections[0]['code'] == sec['code']:
                            isNotExists = False
                            break
                    if isNotExists:
                        secs.extend(sections)
                        try:
                            pg.execute(self.update_sql_secs,json.dumps(secs,ensure_ascii=False),qid)
                        except Exception as e1:
                            logger.error(u'更新题目章节异常，异常信息：%s，题目id：%s，章节信息：%s',
                                             e1.message,qid,json.dumps(secs,ensure_ascii=False))
                            raise e1
                    continue
                # print json.dumps(sections, ensure_ascii=False)
                #获取解析
                analyze_xpath = u"//fieldset[@id='%s']/../div[@class='fieldtip']//i[@class='icon i-analyze']/.." % old_id
                WebDriverWait(driver, 20).until(lambda x: x.find_element_by_xpath(analyze_xpath).is_displayed())
                analyze_ele = driver.find_element_by_xpath(analyze_xpath)
                time.sleep(1)
                # driver.execute(Command.MOVE_TO, analyze_ele.location_once_scrolled_into_view)
                if self.browserType == 2:
                    webdriver.ActionChains(driver).move_to_element(analyze_ele)
                else:
                    webdriver.ActionChains(driver).move_to_element(analyze_ele).perform()
                analyze_ele.click()
                answer, analyses, points =self.getAnswerAndAnalysis(driver,content_arr[-1])
                subject = course[0]
                #设置插入数据
                params = (old_id,answer,analyses,self.cate,self.cate_name,content,options,
                          json.dumps(sections, ensure_ascii=False),points,subject,difficulty,dg,old_id)
                try:
                    pg.execute(self.insert_sql,params)
                    pg.commit()
                except  Exception as e2:
                    pg.rollback()
                    logger.error(u'插入菁优题目异常，异常信息%s,插入数据:%s',e2.message,json.dumps(params,ensure_ascii=False))
                    raise e2
                self.question_count +=1
                if self.question_count >= self.question_Max_count:
                    raise Exception(u'停止爬题，今日爬取数量：%d,已达到最大值：%d' % (self.question_count,self.question_Max_count))

            except Exception as e:
                logger.exception(u'分析题目失败,题目原始网页：%s，错误信息：%s',unicode(li),e.message)
                raise e
        # 下一页
        self.next_page(driver,div_soup,sections)


    def next_page(self,driver,div_soup,sections):
        '''请求下一页'''
        opt_soup = div_soup.find('div',attrs={'class':'page'}).find('option',attrs={'selected':True})
        pages =re.findall('^\s*(\d+?)\s*/\s*(\d+?)\s*$',opt_soup.get_text())[0]
        cur_page = int(pages[0])
        total_pag = int(pages[1])
        # 当前页小于总分页数，并且小于最大允许分页
        if cur_page < total_pag and  cur_page < self.maxPage:
            next_ele = driver.find_element_by_xpath(u"//div[@id='pageArea']/div[@class='page']/div[@class='pagertips']/a[@class='next'][@title='下一页']")
            if self.browserType == 2:
                webdriver.ActionChains(driver).move_to_element(next_ele)
            else:
                webdriver.ActionChains(driver).move_to_element(next_ele).perform()

            # 直接调用函数不调用点击
            # js_goPage = next_ele.get_attribute('href').replace('javascript:','')
            # logger.info(u'调用下一页函数：%s，当前调用的url:%s',js_goPage,driver.current_url)
            # driver.execute_script(js_goPage.replace('this', 'arguments[0]'), next_ele)

            # 可以调用界面点击
            time.sleep(1)
            next_ele.click()
            self.parseQuestionPg(driver,sections,course,pg)

    def getAnswerAndAnalysis(self,driver,content_verify):
        '''获取题目答案与解析'''
        WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath("//div[@class='box-wrapper']").is_displayed())
        time.sleep(1)
        box_wra_elel = driver.find_element_by_xpath("//div[@class='box-wrapper']")
        # with open('text.txt','w') as f: f.write(box_wra_elel.get_attribute('outerHTML'))
        box_wra_html = box_wra_elel.get_attribute('outerHTML')
        # 关闭解析
        hclose_ele = box_wra_elel.find_element_by_xpath(u"//input[@title='关闭']")
        hclose_ele.click()
        # 校验解析是否正常
        if box_wra_html.find(content_verify) == -1 and box_wra_html.find(content_verify.replace('/>','>').replace(u' ','&nbsp;')) == -1.:
            raise Exception(u'获取题目解析异常，答案解析源码是：%s，校验内容是：%s' % (box_wra_html,content_verify))
        #开始分析
        box_soup = BeautifulSoup(box_wra_html,self.features)
        labe_soup = box_soup.find('input', attrs={'checked': 'checked'}, class_="radio s").find_parent()
        answer = re.findall(u'^([A-Z])．.*$',labe_soup.get_text())
        if not answer:
            logger.error(u'获取解析答案异常,解析文本值:%s',labe_soup.get_text())
            raise Exception(u'获取解析答案异常,解析文本值:%s',labe_soup.get_text())
        answer = json.dumps(answer,ensure_ascii=False)
        #解析知识点
        point_soup = box_soup.find('em',text=u'【考点】')
        points = []
        for a_soup in point_soup.find_next_siblings('a'):
            know_name = a_soup.get_text()
            know_id = '0'
            try:
                know_id = re.findall(u"openPointCard\(\s*'[a-zA-Z\d]+?'\s*,\s*'([a-zA-Z\d]+?)'\s*\);\s*return\s*false;\s*",a_soup['onclick'])[0]
            except  Exception as e:
                logger.exception(u'解析获取知识点ID失败,原始文本：%s，错误信息:%s',a_soup['onclick'],e.message)
            points.append({'code':know_id,'name':know_name})
        points = json.dumps(points,ensure_ascii=False)
        analysis_soup = box_soup.find('em',text=u'【分析】').parent
        analysis = re.findall(u'<div\s+class="pt[\d]"\s*>\s*<!--B[\d]-->\s*(.+?)<!--E[\d]-->\s*</div>',unicode(analysis_soup))[0].replace(u'<em>【分析】</em>','')
        return (answer,analysis,points)

if __name__ == '__main__':
    selection = JyeooSelectionQuestion(browserType=2)
    pg = PostgreSql()
    try:
        #查询需要下载菁优题目的学科
        sd_list = []
        for s in pg.getAll(SQL_SUBJECT_DOWLOAD):
            sd_list.append(s[0])
        #开始下载
        c_list = pg.getAll(SQL_SUBJECT)
        for course in c_list:
            if course[0] in sd_list:
                selection.mainSelection(course,pg)
    finally:
        pg.close()
