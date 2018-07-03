#!/usr/bin/python
#-*-coding:utf-8-*-

import requests
import HTMLParser
import re
import time
import datetime
import json
from bs4 import BeautifulSoup #lxml解析器
from utils import LoggerUtil,Utils
from utils.SqlUtil import PostgreSql,MongoDB
from cfg import COLL,URL
from selenium import webdriver
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support.ui import WebDriverWait
import pickle
import random
from ConfigParser import ConfigParser
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
html_parser = HTMLParser.HTMLParser()
logger = LoggerUtil.getLogger(__name__)

#读取配置文件
config = ConfigParser()
config.read('jyeoo.cfg')
SELECTION_JYEOO = 'jyeoo'
def getCFGInt(params_name,default=None): return config.getint(SELECTION_JYEOO,params_name)if config.has_option(SELECTION_JYEOO,params_name) else default
def getCFG(params_name,default=None): return config.get(SELECTION_JYEOO,params_name)if config.has_option(SELECTION_JYEOO,params_name) else default
NO_QUES_MESS=u'对不起，当前条件下没有试题，菁优网正在加速解析试题，敬请期待！'
MAX_PAGE= getCFGInt('max_page',3)
ERR_IDS = config.get(SELECTION_JYEOO,'err_ids').split(',')
EMAIL_NAMES = getCFG('email_names')

SQL_SUBJECT = 'select subject_code,subject_ename,subject_zname from t_subject'
SQL_SUBJECT_DOWLOAD = 'SELECT subject_id FROM t_grade_ek_20180602 WHERE  status = 1 GROUP BY subject_id'
#当前日期
CURR_DATE = datetime.date.today()

'''爬题完成后抛出异常'''
class CompleteException(Exception): pass


def getUser(pg):
    '''获取用户信息'''
    user_dic = {}
    mac_addr = Utils.getMacAddress()
    host_name = Utils.getHostName()
    user_sql = 'select user_name,pass_word,subject_code,browser,is_proxy,proxy_addr,proxy_port,host_name,other_info from t_user WHERE status = %s and host_name = %s'
    user = pg.getOne(user_sql,(1,host_name))
    if user:
        user_dic['other_info'] = user[-1]
    else:
        sub_code = raw_input(u'No binding account found, please enter the subject code: ')
        while True:
            if re.findall('^[1-9][0-9]$',sub_code):
                sub_code = int(sub_code)
                user_sql = 'select user_name,pass_word,subject_code,browser,is_proxy,proxy_addr,proxy_port,host_name,other_info from t_user WHERE status = %s and subject_code = %s'
                user = pg.getOne(user_sql,(0,sub_code))
                if not user:
                    raise Exception(u'学科:%d，没有可用账号！' % sub_code)
                other_info = {u'computerName':host_name,u'mac_addr':mac_addr}
                user_update_sql = 'update t_user set status=%s, host_name=%s,other_info=%s where user_name = %s  '
                try:
                    pg.execute(user_update_sql,(1,host_name,json.dumps(other_info,ensure_ascii=False),user[0]))
                    pg.commit()
                    user_dic['other_info'] = other_info
                except  Exception as e:
                    pg.rollback()
                    raise e
                break
            else:
                sub_code = raw_input(u'The input discipline code format is incorrect, please re-enter the subject code: ')
    user_dic['user_name']=user[0]
    user_dic['pass_word'] = user[1]
    user_dic['subject_code'] = user[2]
    user_dic['browser'] = user[3]
    user_dic['is_proxy'] = user[4]
    user_dic['proxy_addr'] = user[5]
    user_dic['proxy_port'] = user[6]
    user_dic['host_name'] = host_name
    curr_date = CURR_DATE
    # 查询配置
    params = {}
    for row in pg.getAll('select name,value from t_param'):
        params[row[0]] = row[1]
    user_dic['wait_min_time'] = int(params['wait_min_time'])
    user_dic['wait_max_time'] = int(params['wait_max_time'])
    user_dic['session_valid_time'] = int(params['session_valid_time'])
    # 查询生成计划
    plan_sql = 'select ques_total,ques_count,ques_plan,time_plan,status from t_plan where user_name = %s and date >= %s'
    plan = pg.getOne(plan_sql,(user_dic['user_name'],curr_date))
    if not plan:
        #生成执行计划
        user_dic['ques_total'],user_dic['ques_count'],user_dic['ques_plan'],user_dic['time_plan'] =generatePlan(params)
        plan_insert_sql = 'insert into t_plan(user_name,ques_total,ques_count,ques_plan,time_plan,status) ' \
                          'VALUES (%s,%s,%s,%s,%s,%s)'
        try:
            pg.execute(plan_insert_sql, (user_dic['user_name'], user_dic['ques_total'],user_dic['ques_count'],
                                         json.dumps(user_dic['ques_plan']),json.dumps(user_dic['time_plan']),0))
            pg.commit()
        except  Exception as e:
            pg.rollback()
            raise e
    elif plan[-1] == 1:
        logger.info(u"Today's plan has been completed")
        raise Exception(u"Today's plan has been completed")
    else:
        user_dic['ques_total'] = plan[0]
        user_dic['ques_count'] = plan[1]
        user_dic['ques_plan'] = plan[2]
        user_dic['time_plan'] = plan[3]
    return user_dic

def generatePlan(params):
    # 已完成题目数，初始化为0
    ques_count = 0
    #获取题目总数
    ques_total =  random.randint(int(params['ques_total_min']),int(params['ques_total_max']))
    #题目计划
    ques_plan = []
    ques_min = int(params['ques_min'])
    ques_max = int(params['ques_max'])
    ques_alloc = 0
    while (ques_total-ques_alloc) > ques_max:
        ques_alloc += random.randint(ques_min,ques_max)
        ques_plan.append(ques_alloc)
    #时间计划
    count = len(ques_plan)
    wait_avg_time = int(params['wait_time_avg_total'])/count
    time_plan = []
    for i in range(0,count):
        time_plan.append(wait_avg_time+random.randint(-20,20))
    return (ques_total,ques_count,ques_plan,time_plan)

class JyeooSelectionQuestion:
    '''根据章节爬取题目'''
    def __init__(self,pg,features='lxml'):
        '''features BeautifulSoup 解析的方式:html.parser,lxml,lxml-xml,xml
            browserType:浏览器类型 1-chrome 2-Firefox
        '''
        user = getUser(pg)
        self.maxPage = MAX_PAGE
        self.features = features
        self.browserType = user['browser']
        self.user_name = user['user_name']
        self.pass_word = user['pass_word']
        # 当日最大爬题数量、已爬题数量、爬取计划、时间计划,题目最大、最小等待时间、session有效时间（h）
        self.question_Max_count = user['ques_total']
        self.question_count = user['ques_count']
        self.ques_plan = user['ques_plan']
        self.time_plan = user['time_plan']
        self.wait_min_time = user['wait_min_time']
        self.wait_max_time = user['wait_max_time']
        self.session_valid_time = user['session_valid_time']
        #当日时间
        self.curr_date = CURR_DATE

        self.isPorxy = user['is_proxy']
        proxy_host = user['proxy_addr']
        proxy_port = user['proxy_port']
        if self.browserType == 2:
            if self.isPorxy:
                fp = webdriver.FirefoxProfile()
                # Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
                logger.info(u'Firefox 使用代理地址：%s:%d', proxy_host,proxy_port)
                fp.set_preference("network.proxy.type", 1)
                fp.set_preference("network.proxy.http", proxy_host)
                fp.set_preference("network.proxy.http_port", int(proxy_port))
                fp.set_preference("general.useragent.override", "whater_useragent")
                fp.update_preferences()
                self.driver = webdriver.Firefox(firefox_profile=fp)
            else:
                logger.info(u'Firefox 不使用代理')
                self.driver = webdriver.Firefox()
        else:
            if self.isPorxy:
                logger.info(u'chrome 使用代理地址：%s:%d',proxy_host,proxy_port)
                chromeOptions = webdriver.ChromeOptions()
                chromeOptions.add_argument("--proxy-server=http://%s:%d" %(proxy_host,proxy_port))
                self.driver = webdriver.Chrome(chrome_options=chromeOptions)
            else:
                logger.info(u'chrome 不使用代理')
                self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.insert_sql = u'INSERT INTO  t_ques_jyeoo_20180601(qid,answer,analyses,cate,cate_name,content,options,sections,points,subject,difficulty,dg,old_id) ' \
                          'VALUES (uuid_generate_v5(uuid_ns_url(), %s),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        self.insert_sql_section = u'INSERT INTO t_last_section_20180601(section_id,title,status,grade_id) VALUES (%s,%s,%s,%s)'
        self.select_sql = u'SELECT qid,sections FROM t_ques_jyeoo_20180601 WHERE old_id=%s'
        self.select_sql_seciton = u'SELECT section_id,title FROM t_last_section_20180601 WHERE  section_id=%s and status = %s'
        self.update_sql_secs = u"UPDATE t_ques_jyeoo_20180601  SET  sections=%s  WHERE  qid=%s "
        self.cate = 1
        self.cate_name = '单选题'
        self.err_count = 0
        self.__subject_code = user['subject_code']
        logger.info(u'初始化参数,学科代码：%d，最大分页数量：%d，今日最大爬取数量：%d，今日已爬数量：%d',
                    self.__subject_code,self.maxPage,self.question_Max_count,self.question_count)
    def closeDriver(self):
        self.driver.quit()
        # self.driver.close()

    def getSubjectCode(self):
        return self.__subject_code

    def login(self,driver):
        '''用户登录'''
        cookies = None
        vail_info = None
        try:
            cookies = pickle.load(open("%s-cookies.pkl" % self.user_name, "rb"))
            vail_info = pickle.load(open("%s-vail.pkl" % self.user_name, "rb"))
        except Exception as e:
            pass
        #session有效小时内 不用登陆
        if cookies and self.browserType == vail_info['browserType'] \
                and (time.time() - vail_info['last_time']) < 60 * 60 * self.session_valid_time:
            for cookie in cookies:
                driver.add_cookie(cookie)
        else:
            driver.implicitly_wait(10)
            login_xpath = u"//div[@class='top']/div[@class='tr']/a[@href='/account/login']"
            WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(login_xpath).is_displayed())
            login_button = driver.find_element_by_xpath(login_xpath)
            login_button.click()
            #进入登录界面
            pageWait = WebDriverWait(driver, 10)
            pageWait.until(lambda x: x.find_element_by_xpath(u"//iframe[@id='mf']").is_displayed())
            driver.switch_to_frame(frame_reference='mf')
            wexin_xpath = u"//div[@id='divWeixinLogin']//div[@class='s-pc']"
            WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(wexin_xpath).is_displayed())
            wexin_button = driver.find_element_by_xpath(wexin_xpath)
            wexin_button.click()
            acc_input = driver.find_element_by_id('Email')
            pwd_input = driver.find_element_by_id('Password')
            acc_input.send_keys(self.user_name)
            pwd_input.send_keys(self.pass_word)
            while True:
                try:
                    if driver.find_element_by_xpath(u"//div[@class='user']"):
                        logger.info(u'用户确认已登录')
                        break
                except Exception:
                    acc_input = driver.find_element_by_id('Email')
                    pwd_input = driver.find_element_by_id('Password')
                    acc_input.clear()
                    acc_input.send_keys(self.user_name)
                    pwd_input.clear()
                    pwd_input.send_keys(self.pass_word)
                time.sleep(2)
        self.saveCookies(driver)

    def saveCookies(self,driver):
        pickle.dump(driver.get_cookies(), open("%s-cookies.pkl" % self.user_name, "wb"))
        vail_info = {'last_time':time.time(),'browserType':self.browserType}
        pickle.dump(vail_info, open("%s-vail.pkl" % self.user_name, "wb"))

    def mainSelection(self,course,pg):
        if course[0] != self.getSubjectCode():
            raise Exception(u'Download Subject Non-account bound discipline')
        driver = self.driver
        s_main_url = URL.S_MAIN_URL % course[1]
        logger.info(u'科目：%s,url:%s',course[2],s_main_url)
        driver.get(URL.ROOT_URL)
        #登录
        self.login(driver)
        #查询该账号是否已绑定版本
        bind_grade =pg.getOne('select grade_id from t_grade_ek_20180602 WHERE subject_id=%s AND status = 1 AND user_name= %s',(course[0],self.user_name))
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
                select_sql_e = 'select ek_id from t_grade_ek_20180602 WHERE ek_id=%s AND subject_id=%s AND status = 1'
                r = pg.getOne(select_sql_e,(ek_id,course[0]))
                if not r : continue
                # 点击选择教材版本
                driver.implicitly_wait(10)
                WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath("//div[@class='tree-head']").is_displayed())
                time.sleep(random.randint(5,10))
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
                    if bind_grade:
                        if bind_grade[0] != grade_id: continue
                    else:
                        select_sql_g = 'select grade_id,user_name from t_grade_ek_20180602 WHERE grade_id=%s AND ek_id=%s AND subject_id=%s AND status = 1'
                        r = pg.getOne(select_sql_g, (grade_id,ek_id, course[0]))
                        if r and not  r[1]:
                            #没有绑定进行绑定
                            update_sql_g_u =  'UPDATE t_grade_ek_20180602 SET user_name=%s WHERE grade_id=%s AND ek_id=%s AND subject_id=%s '
                            pg.execute(update_sql_g_u,(self.user_name,grade_id,ek_id,course[0]))
                            pg.commit()
                            bind_grade = [grade_id]
                        else: continue

                    #点击选择年级
                    driver.implicitly_wait(10)
                    WebDriverWait(driver, 10).until(lambda x : x.find_element_by_xpath("//div[@class='tree-head']").is_displayed())
                    time.sleep(random.randint(5, 10))
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
                    self.recurSelection(ul_soup,driver,course,pg,grade_id)
                    update_sql_g = 'UPDATE t_grade_ek_20180602 SET status=2  WHERE grade_id=%s AND ek_id=%s AND subject_id=%s '
                    try:
                        pg.execute(update_sql_g,(grade_id,ek_id,course[0]))
                        pg.commit()
                    except Exception as e:
                        pg.rollback()
                        logger.exception(u'学科：%s，版本：%，年级：%s，下载完成标记异常', course[2], ek_name,grade_name)
                    bind_grade = None
        finally:
            self.saveCookies(driver)

    def recurSelection(self,ul_soup,driver,course,pg,grade_id,parent_Id=None,parent_name=None):
        '''按章节获取题目'''
        for li_soup in ul_soup.find_all('li',recursive=False):
            pk = li_soup.a['pk']
            pk_arr = pk.split('~')
            title = li_soup.a['title']
            child_ul_soup = li_soup.find('ul')
            if child_ul_soup:
                if 'expandable' in li_soup['class']:
                    WebDriverWait(driver, 20).until(lambda x: x.find_element_by_xpath(
                        u"//li/a[@pk='%s'][@title='%s']/../div" % (pk, title)).is_displayed())
                    div_ele = driver.find_element_by_xpath(u"//li/a[@pk='%s'][@title='%s']/../div" % (pk, title))
                    if self.browserType == 2:
                        webdriver.ActionChains(driver).move_to_element(div_ele)
                    else:
                        webdriver.ActionChains(driver).move_to_element(div_ele).perform()
                    div_ele.click()
                self.recurSelection(child_ul_soup,driver,course,pg,grade_id,pk_arr[-2],title)
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
                logger.info(u'今日进度：%d/%d  -  学科代码：%d',
                            self.question_count, self.question_Max_count,self.__subject_code )
                try:
                    pg.execute(self.insert_sql_section,(pk,title,status,grade_id))
                    pg.commit()
                except Exception as e:
                    pg.rollback()
                    logger.exception(u'保存last章节下载完成标记异常,pk：%s，title：%s',pk,title)

    def parseQuestionPg(self,driver,sections,course,pg):
        '''分析分页题目'''
        driver.implicitly_wait(10)
        time.sleep(random.randint(10, 20))
        #获取题目信息页面
        pageArea_html = driver.find_element_by_id('pageArea').get_attribute('outerHTML')
        div_soup = BeautifulSoup(pageArea_html, self.features)
        #判断是页面是否有题目
        if pageArea_html.find(NO_QUES_MESS) > -1:
            #没有题目
            logger.info(u'该页面没有题目，%s-%s',course[2],json.dumps(sections,ensure_ascii=False))
            return
        #分析分页页面题目
        pt1_err_count = 0
        for li in div_soup.find_all(name='li',attrs={'class':'QUES_LI'}):
            #分析具体的每一道题目
            try:
                pt1 = unicode(li.find('div',attrs={'class':'pt1'}))
                old_id = li.fieldset['id']
                if old_id in ERR_IDS: continue
                try:
                    content_arr = re.findall(u'^<div\s+class=[\'"]pt1[\'"]>\s*<!--B\d+-->\s*(.*?)<span\s+class=[\'"]qseq[\'"]>[1-9]\d*．</span>(<a\s+(class=[\'"]ques-source[\'"]\s+)?href=.+?>)?(（.+?）)(</a>)?(.+?)<!--E\d+-->\s*</div>$',pt1)[0]
                except IndexError as ie:
                    pt1_err_count +=1
                    logger.warn(u'匹配题干异常，id为:%s，源码为:%s',old_id,pt1)
                    if pt1_err_count <=3 :
                        continue
                    else:
                        raise ie
                # content_arr = re.findall(u'^<div\s+class=[\'"]pt1[\'"]>\s*<!--B\d+-->\s*(.*?)<span\s+class=[\'"]qseq[\'"]>[1-9]\d*．</span>(<a\s+(class=[\'"]ques-source[\'"]\s+)?href=.+?>)?(（.+?）)?(</a>)?(.+?)<!--E\d+-->\s*</div>$',pt1)[0]
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
                    #判断章节是否已添加到题目中
                    isNotExists = True
                    for sec in secs:
                        if sections[0]['code'] == sec['code']:
                            isNotExists = False
                            break
                    if isNotExists:
                        secs.extend(sections)
                        try:
                            pg.execute(self.update_sql_secs,(json.dumps(secs,ensure_ascii=False),qid))
                        except Exception as e1:
                            logger.error(u'更新题目章节异常，异常信息：%s，题目id：%s，章节信息：%s',
                                             e1.message,qid,json.dumps(secs,ensure_ascii=False))
                            raise e1
                    continue

                #查询线上题库题目是否存在，若存在直接添加到题目中
                # TODO 还需实现 若线上库中有题目这不行要下载解析，直接添加到本库中

                # TODO 暂时不做，因为线上题库也不见的精准

                # TODO 待实现 end
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
                if not answer: continue
                subject = course[0]
                #设置插入数据
                params = (old_id,answer,analyses,self.cate,self.cate_name,content,options,
                          json.dumps(sections, ensure_ascii=False),points,subject,difficulty,dg,old_id)
                try:
                    #插入题目
                    pg.execute(self.insert_sql,params)
                    self.question_count += 1
                    # 更新执行计划 ques_count
                    update_plan_sql = 'update t_plan set ques_count = %s,update_time=CURRENT_TIMESTAMP WHERE user_name = %s and date >= %s'
                    if self.question_count >= self.question_Max_count:
                        update_plan_sql = 'update t_plan set ques_count = %s,update_time=CURRENT_TIMESTAMP, status=1 WHERE user_name = %s and date >= %s'
                    pg.execute(update_plan_sql,(self.question_count,self.user_name,self.curr_date))
                    pg.commit()
                except  Exception as e2:
                    logger.error(u'插入菁优题目异常，异常信息%s,插入数据:%s',e2.message,json.dumps(params,ensure_ascii=False))
                    pg.rollback()
                    raise e2
                try:
                    #当题目达到计划数量时程序休息
                    index =  self.ques_plan.index(self.question_count )
                    logger.info(u'今日进度：%d/%d  -  学科代码：%d',
                                self.question_count, self.question_Max_count, self.__subject_code)
                    logger.info(u'Task sleep %s min', self.time_plan[index])
                    pg.close()
                    time.sleep(self.time_plan[index]*60)
                    pg.reConn()
                    logger.info(u'End task sleep')
                except ValueError:
                    pass

                if self.question_count >= self.question_Max_count:
                    logger.info(u"Today's plan has been completed")
                    raise CompleteException(u'停止爬题，今日爬取数量：%d,已达到最大值：%d' % (self.question_count,self.question_Max_count))

            except Exception as e:
                logger.exception(u'分析题目失败,题目原始网页：%s，错误信息：%s',unicode(li),e.message)
                raise e
        # 下一页
        totalQuesN = int(driver.find_element_by_xpath("//td[@id='TotalQuesN']/em").text)
        if totalQuesN > 10:  self.next_page(driver,div_soup,sections)

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
        #随机等待1,5
        time.sleep(random.randint(self.wait_min_time,self.wait_max_time))
        box_wra_elel = driver.find_element_by_xpath("//div[@class='box-wrapper']")
        # with open('text.txt','w') as f: f.write(box_wra_elel.get_attribute('outerHTML'))
        box_wra_html = box_wra_elel.get_attribute('outerHTML')
        # 关闭解析
        hclose_ele = box_wra_elel.find_element_by_xpath(u"//input[@title='关闭']")
        hclose_ele.click()
        # 校验解析是否正常
        if box_wra_html.find(content_verify) == -1 and box_wra_html.find(content_verify.replace('/>','>').replace(u' ','&nbsp;')) == -1.:
            self.err_count +=1
            if self.err_count > 2:
                raise Exception(u'获取题目解析异常，答案解析源码是：%s，校验内容是：%s' % (box_wra_html,content_verify))
            else:
                return (None,None,None)
        self.err_count = 0
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
                know_id = re.findall(u"openPointCard\(\s*'[a-zA-Z\d]+?'\s*,\s*'([\^~\!@\*&#%$\(！a-zA-Z\d]+?)'\s*\);\s*return\s*false;\s*",a_soup['onclick'])[0]
            except  Exception as e:
                logger.exception(u'解析获取知识点ID失败,原始文本：%s，错误信息:%s',a_soup['onclick'],e.message)
            points.append({'code':know_id,'name':know_name})
        points = json.dumps(points,ensure_ascii=False)
        analysis_soup = box_soup.find('em',text=u'【分析】').parent
        analysis = re.findall(u'<div\s+class="pt[\d]"\s*>\s*<!--B[\d]-->\s*(.+?)<!--E[\d]-->\s*</div>',unicode(analysis_soup))[0].replace(u'<em>【分析】</em>','')
        return (answer,analysis,points)

if __name__ == '__main__':
    pg_host = config.get(SELECTION_JYEOO,'pg_host')
    pg_port = config.getint(SELECTION_JYEOO,'pg_port')
    pg = PostgreSql(host=pg_host,port=pg_port)
    selection = None
    try:
        selection = JyeooSelectionQuestion(pg)
        #查询需要下载菁优题目的学科
        sd_list = []
        for s in pg.getAll(SQL_SUBJECT_DOWLOAD):
            sd_list.append(s[0])
        #开始下载
        c_list = pg.getAll(SQL_SUBJECT)
        for course in c_list:
            if course[0] == selection.getSubjectCode() and course[0] in sd_list:
                selection.mainSelection(course,pg)
        logger.info(u'本账号（%s）下、需要爬取版本的题目已全部完成！',selection.user_name)
    except Exception as e:
        #邮件报警
        if not EMAIL_NAMES:
            logger.exception(u'程序异常，没有收件人列表，所以不发邮件！')
        email_host = getCFG('email_host')
        email_port = getCFG('email_port')
        login_user =  getCFG('login_user')
        login_passwd = getCFG('login_passwd')
        if email_host and email_port and login_user and login_passwd:
            email = Utils.Email(email_host,email_port,login_user,login_passwd)
        else:
            email = Utils.Email()
        email_names = EMAIL_NAMES
        hostName = Utils.getHostName()
        if isinstance(e,CompleteException):
            senMsg = u'恭喜今日爬取已完成！主机名：%s，Mac：%s，Ip地址：%s；\n' \
                     u'详细信息：%s'  % (hostName,Utils.getMacAddress(),Utils.getIpAddr(hostName),e.message)
        else:
            senMsg = u'请查看机器，主机名：%s，Mac：%s，Ip地址：%s； \n' \
                 u'错误信息：%s \n' \
                 u'Exception：%s' % (hostName,Utils.getMacAddress(),Utils.getIpAddr(hostName),e.message,e)
        try:
            email.sendmail(email_names,senMsg)
            logger.info( u'程序出现异常的邮件,发送成功！哈哈')
        except Exception as em:
            logger.exception(u'程序出现异常的邮件,发送失败！异常信息：%s',e.message)
    finally:
        pg.close()
        if selection: selection.closeDriver()
