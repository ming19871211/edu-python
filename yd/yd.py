#!/usr/bin/python
#-*-coding:utf-8-*-

#!/usr/bin/python
#-*-coding:utf-8-*-

import threading
import HTMLParser
import re
import time
import os
import random
import pickle
import datetime
import json
from bs4 import BeautifulSoup #lxml解析器
from utils import LoggerUtil,Utils
from utils.SqlUtil import Mysql
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import Tkinter as tkinter
import tkMessageBox as tkMessageBox
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
#直播并发数量
LIVE_CONCURRENT_NUMBER =  int(getCFG('LIVE_CONCURRENT_NUMBER',5))
#等待下载最大时间
WAIT_DOWNLOAD_MAX_TIME = int(getCFG('WAIT_DOWNLOAD_MAX_TIME',600))
client_phone = getCFG('CLIENT_PHONE')
#回顾的查询语句
SELECT_SQL = "select id,generate_url,course_id,class_room_id,user_name,user_id,user_mobile,play_time from t_hzb_course WHERE state='%s'  and start_time<= now() and end_time >= now()  ORDER BY start_time asc limit %s"
#直播的查询语句
LIVE_SELECT_SQL = "select id,generate_url,course_id,class_room_id,user_name,user_id,user_mobile,play_time from t_hzb_course WHERE state=%s and play_type=1  and live_start_time<= now() and live_end_time >= now() ORDER BY rand() limit %s"

total = 0
fail_total = 0
#版本号、版本等级
VERSION = "1.5.1"
VERSION_LEVEL = 5

class YD:
    def __init__(self):
        path_str = os.getenv('path')
        pwd_str = os.getcwd()
        if path_str.find(pwd_str) == -1:
            sys.path.append(pwd_str)
        self.__execInitParams()
        if client_phone:
            self.CLIENT_PHONE = client_phone
            self.CONCURRENT_NUMBER = CONCURRENT_NUMBER
            self.LIVE_CONCURRENT_NUMBER = LIVE_CONCURRENT_NUMBER
        else:
            self.__inputPhone()

    def __on_click(self):
        self.CLIENT_PHONE = self.__phone_text.get().lstrip()
        if len(self.CLIENT_PHONE) == 0:
            tkMessageBox.showerror(u'错误', u'手机号码必须输入')
            logger.error(u"手机号码必须输入!")
            return
        else:
            phone_pat = re.compile('^(1[3-9]\d)\d{8}$')
            res = re.search(phone_pat, self.CLIENT_PHONE)
            if not res:
                tkMessageBox.showerror(u'错误', u'手机号码格式不正确！')
                self.CLIENT_PHONE = None
                logger.error(u"手机号码格式不正确！")
                return
        #回顾并发数
        concurrent_number = self.__concurrent_number.get().lstrip()
        if len(concurrent_number) == 0:
            tkMessageBox.showerror(u'错误', u'开启浏览器回顾数量必须输入')
            logger.error(u"开启浏览器回顾数量必须输入!")
            return
        else:
            concurrent_pat = re.compile('^[1-9][0-5]?$')
            res_c = re.search(concurrent_pat, concurrent_number)
            if not res_c:
                tkMessageBox.showerror(u'错误', u'开启浏览器回顾数必须为1到15之间的数值')
                self.CLIENT_PHONE = None
                logger.error(u"开启浏览器回顾数必须为1到15之间的数值！")
                return
        self.CONCURRENT_NUMBER = int(concurrent_number)

        # 直播并发数
        live_concurrent_number = self.__live_concurrent_number.get().lstrip()
        if len(live_concurrent_number) == 0:
            tkMessageBox.showerror(u'错误', u'开启浏览器直播数量必须输入')
            logger.error(u"开启浏览器直播数量必须输入!")
            return
        else:
            live_concurrent_pat = re.compile('^[1-9][0-5]?$')
            res_c_l = re.search(live_concurrent_pat, live_concurrent_number)
            if not res_c_l:
                tkMessageBox.showerror(u'错误', u'开启浏览器直播数必须为1到15之间的数值')
                self.CLIENT_PHONE = None
                logger.error(u"开启浏览器直播数必须为1到15之间的数值！")
                return
        self.LIVE_CONCURRENT_NUMBER = int(live_concurrent_number)

        #保留最后一次输入的手机号码、并发数
        self.__saveInfo(clientPhone=self.CLIENT_PHONE,concurrent_number=self.CONCURRENT_NUMBER,live_concurrent_number=self.LIVE_CONCURRENT_NUMBER)
        self.__tk.quit()
        self.__tk.destroy()
    def __saveInfo(self,clientPhone=None,concurrent_number=None,live_concurrent_number=None):
        my_yd_info = {'CLIENT_PHONE': clientPhone,'CONCURRENT_NUMBER':concurrent_number,'LIVE_CONCURRENT_NUMBER':live_concurrent_number}
        pickle.dump(my_yd_info, open("my-yd-info.pkl","wb"))
    def __getInfoPhone(self):
        try:
            my_yd_info = pickle.load(open("my-yd-info.pkl","rb"))
            return my_yd_info['CLIENT_PHONE']
        except Exception:
            return ' '
    def __getInfoConcurrentNumber(self):
        try:
            my_yd_info = pickle.load(open("my-yd-info.pkl","rb"))
            return my_yd_info['CONCURRENT_NUMBER']
        except Exception:
            return CONCURRENT_NUMBER if CONCURRENT_NUMBER >= 1 and CONCURRENT_NUMBER <= 15 else 15
    def __getInfoLiveConcurrentNumber(self):
        try:
            my_yd_info = pickle.load(open("my-yd-info.pkl","rb"))
            return my_yd_info['LIVE_CONCURRENT_NUMBER']
        except Exception:
            return LIVE_CONCURRENT_NUMBER if LIVE_CONCURRENT_NUMBER >= 1 and LIVE_CONCURRENT_NUMBER <= 15 else 15

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
        # 输入手机号码
        self.__phone_text = tkinter.StringVar()
        entry = tkinter.Entry(tk, textvariable=self.__phone_text)
        self.__phone_text.set(self.__getInfoPhone())
        entry.pack()
        #输入CONCURRENT_NUMBER
        ll2 = tkinter.Label(tk, text=u"同时开启回顾浏览器数量")
        ll2.pack()
        self.__concurrent_number = tkinter.StringVar()
        entry_concurrent = tkinter.Entry(tk, textvariable=self.__concurrent_number)
        self.__concurrent_number.set(self.__getInfoConcurrentNumber())
        entry_concurrent.pack()
        # 输入CONCURRENT_NUMBER
        ll3 = tkinter.Label(tk, text=u"同时开启直播浏览器数量")
        ll3.pack()
        self.__live_concurrent_number = tkinter.StringVar()
        entry_live_concurrent = tkinter.Entry(tk, textvariable=self.__live_concurrent_number)
        self.__live_concurrent_number.set(self.__getInfoLiveConcurrentNumber())
        entry_live_concurrent.pack()
        #确认按钮
        tkinter.Button(tk, text=u"点击确认", command=self.__on_click).pack()
        tk.mainloop()
        if not self.CLIENT_PHONE:
            tkMessageBox.showerror(u'错误', u'手机号码或浏览器数量必须输入！')
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
                elif param_name == 'min_live_play_time':
                    self.__min_live_play_time = int(param_value)
                elif param_name == 'max_live_play_time':
                    self.__max_live_play_time = int(param_value)
                elif param_name == 'process_max_num':
                    self.__process_max_num = int(param_value)
                elif param_name == 'process_pause_time':
                    self.__process_pause_time = int(param_value)
                elif param_name == 'not_limit_phones':
                    self.__not_limit_phones = param_value.split(',')
            self.__query_time = time.time()
            #检查版本
            if self.__support_level > VERSION_LEVEL:
                message = u'请升级到最新版本:%s，当前版本%s，下载地址见文档:http://doc.pages.talkedu.cn/hzb/' %(self.__last_version,VERSION)
                tkMessageBox.showerror(u'错误', message)
                logger.error(message)
                exit(-1)
        finally:
            mysql.close()

    def isNotRunTime(self):
        curr_time = time.time()
        if curr_time - 60*60*2 > self.__query_time:
            self.__execInitParams()
        play__end_time =  Utils.gettime(self.__end_time-1,59,59) if self.__end_time == 24 else  Utils.gettime(self.__end_time)
        if curr_time < Utils.gettime(self.__start_time) or curr_time > play__end_time:
            logger.info(u'已进入夜间休息时间[%d点-%d点]，播放程序不会进行播放', self.__end_time, self.__start_time)
            return True
        else:
            return False
    def isOutMaxProcessNum(self):
        '''是否超出最大占用数'''
        sql = 'SELECT count(1) FROM `t_hzb_course` where client_phone=%s and state =%s'
        mysql = Mysql()
        try:
            num = mysql.getOne(sql,(self.CLIENT_PHONE,1))
        except:
            mysql.close()
        if num > self.__process_max_num:
            logger.warning(u'您播放刷课失败次数太多，当前占用的刷课数量%d大于最大刷课占用数量%d，暂时暂停您的播放时间%dmim。请检查您的电脑和网络是否有问题！',
                           num,self.__process_max_num,self.__process_pause_time)
            # tk = tkinter.Tk()
            # tkMessageBox.showinfo(u'错误', '请检查您的电脑和网络是否有问题！')
            # tk.destroy()
            # exit(-1)
            time.sleep(self.__process_pause_time*60)
            logger.info(u'暂停时间到了，恢复您的刷课播放！')
            return True

    def scrapyAll(self,select_sql=SELECT_SQL,live_select_sql=LIVE_SELECT_SQL,thread_num=None,live_thread_num=None):
        thread_num = thread_num if thread_num else self.CONCURRENT_NUMBER
        live_thread_num = live_thread_num if live_thread_num else self.LIVE_CONCURRENT_NUMBER
        logger.info(u'[您已成功开启和教育直播视频软件正式版本]--您的手机号是:%s 当前运行版本:%s 最新版本:%s 回顾开启浏览器数:%s 直播开启浏览器数量:%s',
                    self.CLIENT_PHONE,VERSION,self.__last_version,thread_num,self.LIVE_CONCURRENT_NUMBER)
        count = 1
        process_loop_num =0
        global total,fail_total
        while count:
            count = 0
            if self.isNotRunTime(): break
            # 检验此手机号码刷课是否存在异常,每循环3次检查一次
            if self.CLIENT_PHONE not in self.__not_limit_phones \
                    and  process_loop_num%3 == 0 and self.isOutMaxProcessNum():
                process_loop_num = 0
                break
            else:
                process_loop_num += 1
            mysql = Mysql()
            try:
                #获取直播数据
                rows = mysql.getAll(live_select_sql, (0,live_thread_num))
                if rows:
                    self.is_live = True
                else:
                    self.is_live = False
                    #获取回顾数据
                    rows = mysql.getAll(select_sql,(0,thread_num))
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
                        YDThread(rs,self.CLIENT_PHONE,self.is_live,self.__min_live_play_time,self.__max_live_play_time).start()
                else:
                    logger.info(u'客服端手机号码:%s,当前时间已没有可以播放的直播或者回顾的视频了哦！',self.CLIENT_PHONE)
                    break
            finally:
                mysql.close()
            for t in threading.enumerate():
                if t is threading.currentThread():
                    continue
                t.join()
            total += count
            logger.info(u'客服端手机号码:%s,合计处理访问数量%d，成功数量%d，失败数量:%d',self.CLIENT_PHONE,total,total-fail_total,fail_total)

class YDThread(threading.Thread):
    def __init__(self,rs,CLIENT_PHONE,is_live,min_live_play_time,max_live_play_time):
        threading.Thread.__init__(self)
        self.rs = rs
        self.CLIENT_PHONE = CLIENT_PHONE
        self.is_live = is_live
        self.min_live_play_time= min_live_play_time
        self.max_live_play_time = max_live_play_time

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
            but_a_xpath = "//div[@class='neirong']//a[@href='javascript:toWatch(%s,%s);'][@class='but_a']" % (course_id, class_room_id) if self.is_live \
                else "//div[@class='neirong']//a[@href='javascript:toReview(%s,%s);'][@class='but_a']" %(course_id,class_room_id)
            WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(but_a_xpath).is_displayed())
            but_a = driver.find_element_by_xpath(but_a_xpath)
            webdriver.ActionChains(driver).move_to_element(but_a).perform()
            but_a.click()
            if self.is_live: #直播
                #监听是否已开始播放了
                sys_info_xpath = '//div[@class="system_info de"]'
                wait_start_time = time.time()
                while True:
                    try:
                        WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(sys_info_xpath).is_displayed())
                        sys_info = driver.find_element_by_xpath(sys_info_xpath)
                        if sys_info.get_attribute('style') == 'display: block; top: 0px;':
                            logger.info(u'%s-%s,直播已经开始播放了哦', user_name, user_mobile)
                            break
                        else:
                            logger.info(u'%s-%s,直播并没有播放了哦', user_name, user_mobile)
                    except  Exception:
                        pass
                    if time.time() - wait_start_time > WAIT_DOWNLOAD_MAX_TIME:
                        raise Exception(u'等待“直播”播放时间超时，超过了最大等待下载时间 %d s' % WAIT_DOWNLOAD_MAX_TIME)
                # 监听实际播放时长哦
                live_play_time = random.randint(self.min_live_play_time,self.max_live_play_time)   #随机获取播放时间
                start_time = time.time()
                real_play_time = time.time() - start_time
                # 防止睡眠时间太长无法唤醒
                while real_play_time < live_play_time:
                    time.sleep(5)
                    real_play_time = time.time() - start_time
                logger.info(u'%s-%s,播放结束哦了！目标播放时间：%d s，实际播放时间: %d s', user_name, user_mobile, live_play_time, real_play_time)
            else:
                #查看是否在播放中
                playBtn_xpath = "//a[@id='playBtn']"
                time.sleep(100)
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
                real_play_time = time.time() - start_time
                #防止睡眠时间太长无法唤醒
                while real_play_time < play_time:
                    time.sleep(5)
                    real_play_time = time.time()-start_time
                logger.info(u'%s-%s,播放结束哦了！目标播放时间：%d s，实际播放时间: %d s',user_name,user_mobile,play_time,real_play_time)
            mysql = Mysql()
            try:
                sql = "update t_hzb_course set state=%s,real_play_time=%s,modify_time=now(),client_phone=%s,play_type=%s WHERE id=%s and user_id=%s"
                mysql.execute(sql,(2,real_play_time,self.CLIENT_PHONE,1 if self.is_live else 0,id,user_id))
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
    sleep_time= 5
    error_time= 1
    while True:
        try:
            yd.scrapyAll()
            logger.info(u'本次检测处理已全部完成，%d分钟后进行下次检测处理。',sleep_time)
            time.sleep(60 * sleep_time)
        except Exception:
            logger.exception(u'刷课程序出现异常哦！%d分钟后将重新处理 ',error_time)
            time.sleep(60 * error_time)
