#!/usr/bin/python
#-*-coding:utf-8-*-

#!/usr/bin/python
#-*-coding:utf-8-*-

import threading
import HTMLParser
import re
import time
import os
import datetime
import json
from bs4 import BeautifulSoup #lxml解析器
from utils import LoggerUtil,Utils
from utils.SqlUtil import Mysql
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import tkinter
import tkinter.messagebox
from ConfigParser import ConfigParser
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
html_parser = HTMLParser.HTMLParser()
logger = LoggerUtil.getLogger(__name__)
SELECT_SQL = "select id,generate_url,course_id,class_room_id,user_name,user_id,user_mobile,play_time from t_hzb_course WHERE state='%s'  and start_time<= now() and end_time >= now()  ORDER BY start_time asc limit %s"

#读取配置文件
cfg = ConfigParser()
cfg.read('yd.cfg')
SECTION_TYPE = "yd"
def getCFG(option,defalut=None): return cfg.get(SECTION_TYPE,option) if cfg.has_option(SECTION_TYPE,option) else defalut
#并发数量
CONCURRENT_NUMBER =  int(getCFG('CONCURRENT_NUMBER',5))
#等待下载最大时间
WAIT_DOWNLOAD_MAX_TIME = int(getCFG('WAIT_DOWNLOAD_MAX_TIME',600))
client_phone = getCFG('CLIENT_PHONE')
total = 0
fail_total = 0
#版本号、版本等级
VERSION = "1.2.2"
VERSION_LEVEL = 2


class YD:
    def __init__(self):
        path_str = os.getenv('path')
        pwd_str = os.getcwd()
        if path_str.find(pwd_str) == -1:
            sys.path.append(pwd_str)
        self.__execInitParams()
        if client_phone:
            self.CLIENT_PHONE = client_phone
        else:
            self.__inputPhone()

    def __on_click(self):
        self.CLIENT_PHONE = self.__phone_text.get().lstrip()
        if len(self.CLIENT_PHONE) == 0:
            tkinter.messagebox.showerror(u'错误', u'手机号码必须输入')
            logger.error(u"手机号码必须输入!")
            return
        else:
            phone_pat = re.compile('^(1[3-9]\d)\d{8}$')
            res = re.search(phone_pat, self.CLIENT_PHONE)
            if not res:
                tkinter.messagebox.showerror(u'错误', u'手机号码格式不正确！')
                self.CLIENT_PHONE = None
                logger.error(u"手机号码格式不正确！")
                return
        self.__tk.quit()
        self.__tk.destroy()

    def __inputPhone(self):
        self.CLIENT_PHONE = None
        tk = tkinter.Tk()
        self.__tk = tk
        tk.geometry("300x150+300+150")
        # 标题
        tk.title(u"输入手机号码")
        # 标签
        ll = tkinter.Label(tk,text=u"请输入你的手机号码：")
        ll.pack()  # 这里的side可以赋值为LEFT  RTGHT TOP  BOTTOM
        # 输入问题类型
        self.__phone_text = tkinter.StringVar()
        entry = tkinter.Entry(tk, textvariable=self.__phone_text)
        self.__phone_text.set(" ")
        entry.pack()
        #确认按钮
        tkinter.Button(tk, text=u"点击确认", command=self.__on_click).pack()
        tk.mainloop()
        if not self.CLIENT_PHONE:
            tkinter.messagebox.showerror(u'错误', u'手机号码必须输入！')
            logger.error(u"手机号码必须输入，退出程序")
            exit(-1)
    def __execInitParams(self):
        '''初始化参数'''
        mysql = Mysql()
        try:
            for p in mysql.getAll('select param_name,param_value from t_hzb_param where enable=1'):
                param_name, param_value = p
                if param_name == 'start_time':
                    self.__start_time = int(param_value)
                elif param_name == 'end_time':
                    self.__end_time = int(param_value)
                elif param_name == 'last_version':
                    self.__last_version = param_value
                elif param_name == 'support_level':
                    self.__support_level = int(param_value)
            self.__query_time = time.time()
            #检查版本
            if self.__support_level > VERSION_LEVEL:
                message = u'请升级到最新版本:%s，当前版本%s，下载地址见文档:http://doc.pages.talkedu.cn/hzb/' %(self.__last_version,VERSION)
                tkinter.messagebox.showerror(u'错误', message)
                logger.error(message)
                exit(-1)
        finally:
            mysql.close()

    def isNotRunTime(self):
        curr_time = time.time()
        if curr_time - 60*60 > self.__query_time:
            self.__execInitParams()
        if curr_time < Utils.gettime(self.__start_time) or curr_time > Utils.gettime(self.__end_time):
            logger.info(u'已进入夜间休息时间[%d点-%d点]，播放程序不会进行播放', self.__end_time, self.__start_time)
            return True
        else:
            return False

    def scrapyAll(self,select_sql=SELECT_SQL,thread_num=CONCURRENT_NUMBER):
        logger.info(u'您已成功开启和教育直播视频软件，你的手机号是:%s，当前运行版本：%s，最新版本：%s',self.CLIENT_PHONE,VERSION,self.__last_version)
        count = 1
        global total,fail_total
        while count:
            count = 0
            if self.isNotRunTime(): break
            mysql = Mysql()
            try:
                rows =  mysql.getAll(select_sql,(0,thread_num))
                if rows:
                    params = []
                    for rs in rows:
                        count += 1
                        id, generate_url, course_id, class_room_id, user_name, user_id, user_mobile, play_time = rs
                        params.append((1,self.CLIENT_PHONE, id, user_id))
                    try:
                        sql = "update t_hzb_course set state=%s,modify_time=now(),client_phone=%s WHERE id=%s and user_id=%s"
                        mysql.batchExecute(sql,params)
                        mysql.commit()
                    except Exception:
                        mysql.rollback()
                        logger.exception(u'修改数据状态异常！')
                    for rs in rows:
                        YDThread(rs,self.CLIENT_PHONE).start()
            finally:
                mysql.close()
            for t in threading.enumerate():
                if t is threading.currentThread():
                    continue
                t.join()
            total += count
            logger.info(u'客服端手机号码:%s,合计处理访问数量%d，成功数量%d，失败数量:%d',self.CLIENT_PHONE,total,total-fail_total,fail_total)

class YDThread(threading.Thread):
    def __init__(self,rs,CLIENT_PHONE):
        threading.Thread.__init__(self)
        self.rs = rs
        self.CLIENT_PHONE = CLIENT_PHONE

    def __startChrome(self):
        # 启动chrome的flash播放器
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
            "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
            "PluginsAllowedForUrls":"https://edu10086.gensee.com"
        }
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_experimental_option('prefs', prefs)
        driver = webdriver.Chrome(chrome_options=chromeOptions)
        return driver

    def __closeChrome(self,driver):
        try:
            driver.quit()
            logger.info(u'正常关闭浏览器')
        except Exception:
            logger.exception(u'关闭浏览器识别哦！')

    def run(self):
        id,generate_url, course_id, class_room_id, user_name, user_id, user_mobile, play_time = self.rs
        try:
            driver = self.__startChrome()
            driver.maximize_window()
            driver.get(generate_url)
            driver.implicitly_wait(10)
            #选择需要播放的视频
            but_a_xpath = "//div[@class='neirong']//a[@href='javascript:toReview(%s,%s);'][@class='but_a']" %(course_id,class_room_id)
            WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(but_a_xpath).is_displayed())
            but_a = driver.find_element_by_xpath(but_a_xpath)
            webdriver.ActionChains(driver).move_to_element(but_a).perform()
            but_a.click()
            #查看是否在播放中
            playBtn_xpath = "//a[@id='playBtn']"
            WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(playBtn_xpath).is_displayed())
            playBtn = driver.find_element_by_xpath(playBtn_xpath)
            webdriver.ActionChains(driver).move_to_element(playBtn).perform()
            isNotPlay = True
            #开始等待的下载时间
            wait_start_time=time.time()
            while isNotPlay:
                logger.info(u'%s-%s,等待下载中...%s',user_name,user_mobile,playBtn.get_attribute('class'))
                isNotPlay =  "play_btn gs-icon-pause" != playBtn.get_attribute('class')
                if time.time() - wait_start_time > WAIT_DOWNLOAD_MAX_TIME:
                    raise Exception(u'等待播放时间超时，超过了最大等待下载时间 %d s'% WAIT_DOWNLOAD_MAX_TIME)
                time.sleep(2)
            #监听实际播放时长哦
            start_time = time.time()
            logger.info(u'%s-%s,开始播放了哦',user_name,user_mobile)
            time.sleep(play_time)
            end_time = time.time()
            real_play_time = end_time-start_time
            logger.info(u'%s-%s,播放结束哦了！目标播放时间：%d s，实际播放时间: %d s',user_name,user_mobile,play_time,real_play_time)
            mysql = Mysql()
            try:
                sql = "update t_hzb_course set state=%s,real_play_time=%s,modify_time=now(),client_phone=%s WHERE id=%s and user_id=%s"
                mysql.execute(sql,(2,real_play_time,self.CLIENT_PHONE,id,user_id))
                mysql.commit()
            except Exception:
                mysql.rollback()
                logger.exception(u'观看视频完成更新时异常')
            finally:
                mysql.close()
        except Exception as e:
            global fail_total
            fail_total += 1
            logger.exception(u'视频播放出现问题！,异常信息:%s',e.message)
        finally:
            self.__closeChrome(driver)

if __name__ == '__main__':
    yd = YD()
    while True:
        try:
            yd.scrapyAll()
            logger.info(u'本次处理已全部完成，30分钟后进行下次处理。')
        except Exception:
            logger.exception(u'爬虫出现异常哦！30分钟后将重新处理 ')
        time.sleep(60*30)