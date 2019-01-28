#!/usr/bin/python
#-*-coding:utf-8-*-

import threading
import HTMLParser
import re
import requests
import time
import os
import random
import pickle
import datetime
import json
from bs4 import BeautifulSoup #lxml解析器
from utils import LoggerUtil,Utils
from ip_proxy import *
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import webbrowser
import Tkinter as tkinter
import tkMessageBox as tkMessageBox
from ConfigParser import ConfigParser
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
html_parser = HTMLParser.HTMLParser()
logger = LoggerUtil.getLogger(__name__)

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
WAIT_DOWNLOAD_MAX_TIME = int(getCFG('WAIT_DOWNLOAD_MAX_TIME',300))
client_phone = getCFG('CLIENT_PHONE')

URL_HOST = getCFG('URL_HOST','hzb.ucenter.talkedu.cn')
# URL_HOST = '192.168.26.30:8080/lsmb-wechat/'
#获取和直播参数
URL_HZB_PARAMS='http://'+URL_HOST+'/course/queryHzbparams'
#获取课程
URL_HZB_COURSE='http://'+URL_HOST+'/course/queryHzbCourseInfo?clientPhone=%s&hbQueryNum=%s&zbQueryNum=%s'
#更新状态
URL_UPDATE_COURSE='http://'+URL_HOST+'/course/updateHzbCourseState?id=%s&userId=%s&state=%s&playType=%s&realPlayTime=%s&clientAddr=%s'
#更新异常状态为未播放
URL_UPDATE_ERR_COURSE='http://'+URL_HOST+'/course/updateHzbCourseState?id=%s&userId=%s&state=%s'
total = 0
fail_total = 0
#版本号、版本等级
VERSION = "1.10.1"
VERSION_LEVEL = 10
REAL_CLIENT_ADDR=None
class HZB:
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
        pickle.dump(my_yd_info, open("hzb-info.pkl.pkl","wb"))
    def __getInfoPhone(self):
        try:
            my_yd_info = pickle.load(open("hzb-info.pkl.pkl","rb"))
            return my_yd_info['CLIENT_PHONE']
        except Exception:
            return ' '
    def __getInfoConcurrentNumber(self):
        try:
            my_yd_info = pickle.load(open("hzb-info.pkl.pkl","rb"))
            return my_yd_info['CONCURRENT_NUMBER']
        except Exception:
            return CONCURRENT_NUMBER if CONCURRENT_NUMBER >= 1 and CONCURRENT_NUMBER <= 15 else 15
    def __getInfoLiveConcurrentNumber(self):
        try:
            my_yd_info = pickle.load(open("hzb-info.pkl.pkl","rb"))
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
        print URL_HZB_PARAMS
        rs = requests.get(URL_HZB_PARAMS).json()
        if rs['code'] == '0':
            for p in rs['data']:
                param_name = p['paramName']
                param_value = p['paramValue']
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
                elif param_name == 'min_play_time':
                    self.__min_play_time = int(param_value)
                elif param_name == 'max_play_time':
                    self.__max_play_time = int(param_value)
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
                webbrowser.open_new('http://doc.pages.talkedu.cn/hzb/')
                exit(-1)
        else:
            logger.error(u'获取初始化参数失败,返回错误信息%s',rs['msg'])
            raise Exception(u'获取初始化参数失败')

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

    def scrapyAll(self,query_course=URL_HZB_COURSE,thread_num=None,live_thread_num=None):
        thread_num = thread_num if thread_num else self.CONCURRENT_NUMBER
        live_thread_num = live_thread_num if live_thread_num else self.LIVE_CONCURRENT_NUMBER
        logger.info(u'[您已成功开启和教育直播视频软件正式版本]--您的手机号是:%s 当前运行版本:%s 最新版本:%s 回顾开启浏览器数:%s 直播开启浏览器数量:%s',
                    self.CLIENT_PHONE,VERSION,self.__last_version,thread_num,self.LIVE_CONCURRENT_NUMBER)
        count = 1
        global total,fail_total
        while count:
            count = 0
            if self.isNotRunTime(): break
            res = requests.get(query_course %(self.CLIENT_PHONE,self.CONCURRENT_NUMBER,self.LIVE_CONCURRENT_NUMBER))
            rs = res.json()
            if rs['code'] == '0':
                rows = rs['data']
                if rows:
                    for r in rows:
                        HZBThread(r,self.CLIENT_PHONE, self.__min_live_play_time, self.__max_live_play_time,self.__min_play_time,self.__max_play_time).start()
                        count+=1
                else:
                    logger.info(u'客服端手机号码:%s,当前时间已没有可以播放的直播或者回顾的视频了哦！', self.CLIENT_PHONE)
                    break
            else:
                logger.error(u'获取课程异常，异常信息：%s',rs['msg'])
            for t in threading.enumerate():
                if t is threading.currentThread():
                    continue
                t.join()
            total += count
            logger.info(u'客服端手机号码:%s,合计处理访问数量%d，成功数量%d，失败数量:%d',self.CLIENT_PHONE,total,total-fail_total,fail_total)

class HZBThread(threading.Thread):
    def __init__(self,rs,CLIENT_PHONE,min_live_play_time,max_live_play_time,min_play_time,max_play_time):
        threading.Thread.__init__(self)
        self.rs = rs
        self.CLIENT_PHONE = CLIENT_PHONE
        self.min_live_play_time= min_live_play_time
        self.max_live_play_time = max_live_play_time
        self.min_play_time=min_play_time
        self.max_play_time=max_play_time

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
        proxies = None
        if self.rs['clientIp'] and self.rs['port']:
            logger.info('代理IP：%s:%s', self.rs['clientIp'], self.rs['port'])
            chromeOptions.add_argument("--proxy-server=http://%s:%s" % (self.rs['clientIp'],self.rs['port']))
            # chromeOptions.add_argument('%s=%s' % self.ip_info['proxy-auth'])
            proxies={'http': 'http://%s:%s'%(self.rs['clientIp'],self.rs['port'])}
        #获取请求的IP地址
        if proxies:
            err_count = 0
            while err_count < 3:
                try:
                    respon = requests.get('http://www.cip.cc',proxies=proxies,timeout=5)
                    str = re.findall(u'<div\s*class="data\s*kq-well">\s*<pre>(.+?)</pre>\s*</div>', respon.text, re.M | re.S | re.I)[0]
                    self.address = re.findall(u'数据三\s*:\s*(.+?)\n', str, re.M)[0]
                    break;
                except Exception as e:
                    err_count +=1
                    if err_count >=3:
                        logger.exception(u'网络连接异常：代理IP：%s:%s',self.rs['clientIp'],self.rs['port'])
                        raise e
        else:
            global REAL_CLIENT_ADDR
            self.address = REAL_CLIENT_ADDR
        driver = webdriver.Chrome(chrome_options=chromeOptions)
        return driver

    def __closeChrome(self,driver):
        try:
            driver.quit()
            logger.info(u'正常关闭浏览器')
        except Exception:
            logger.exception(u'关闭浏览器识别哦！')

    def run(self):
        id,generate_url,course_id, class_room_id, user_name, user_id, user_mobile, play_time = \
            (self.rs['id'],self.rs['generateUrl'],self.rs['courseId'],self.rs['classRoomId'],self.rs['userName'],
             self.rs['userId'],self.rs['userMobile'],self.rs['playTime'])
        try:
            logger.info(u'准备开启浏览器了')
            driver = self.__startChrome()
            driver.maximize_window()
            generate_url = generate_url.replace('&amp;','&')
            driver.get(generate_url)
            driver.implicitly_wait(10)
            #选择需要播放的视频
            but_a_xpath = "//div[@class='neirong']//a[@href='javascript:toWatch(%s,%s);'][@class='but_a']" % (course_id, class_room_id) if self.rs['playType'] == 1 \
                else "//div[@class='neirong']//a[@href='javascript:toReview(%s,%s);'][@class='but_a']" %(course_id,class_room_id)
            WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath(but_a_xpath).is_displayed())
            but_a = driver.find_element_by_xpath(but_a_xpath)
            #元素滚动到最顶端
            driver.execute_script("arguments[0].scrollIntoView(true);",but_a)
            webdriver.ActionChains(driver).move_to_element(but_a).perform()
            but_a.click()
            if self.rs['playType'] == 1: #直播
                logger.info(u'进入直播播放')
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
                logger.info(u'进入回顾播放')
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
                real_play_time = time.time() - start_time
                time_one1_xpath = "//div[@class='play_time']/span[@class='time_one1']"
                time_one1 = driver.find_element_by_xpath(time_one1_xpath)
                #随机生成回顾播放时间
                play_time = play_time if (play_time and play_time) > 0  else random.randint(self.min_play_time, self.max_play_time)  # 随机获取播放时间
                #防止睡眠时间太长无法唤醒
                curr_play_time =  -1
                while real_play_time < play_time:
                    tmp_play_time =  getSecond(time_one1.text)
                    if tmp_play_time <= curr_play_time:
                        curr_play_time = tmp_play_time
                        logger.error(u'播放出现了停止现象！')
                        if curr_play_time > self.min_play_time:
                            break
                        else:
                            raise Exception(u'播放出现了停止现象！%s-%s 实际播放时间:%d s',user_name,user_mobile,curr_play_time)
                    else:
                        curr_play_time = tmp_play_time
                        if curr_play_time >= play_time:
                            real_play_time = curr_play_time
                            break
                    time.sleep(5)
                    real_play_time = time.time()-start_time
                logger.info(u'%s-%s,播放结束哦了！目标播放时间：%d s，实际播放时间: %d s',user_name,user_mobile,play_time,real_play_time)
            try:
                url_update_course= URL_UPDATE_COURSE %(id,user_id,2,self.rs['playType'],int(real_play_time),self.address)
                if self.rs['clientIp'] and self.rs['port']:
                    url_update_course += u'&clientIp=%s&port=%s'%(self.rs['clientIp'],self.rs['port'])
                rs = requests.get(url_update_course)
            except Exception:
                logger.exception(u'观看视频完成更新时异常')
        except Exception as e:
            global fail_total
            fail_total += 1
            logger.exception(u'视频播放出现问题！,异常信息:%s',e.message)
            rs = requests.get(URL_UPDATE_ERR_COURSE % (id, user_id, 0))
            print rs.text
        finally:
            self.__closeChrome(driver)

def getSecond(str):
    (a,b)=str.split(':')
    return int(a)*60+int(b)

if __name__ == '__main__':
    respon = requests.get('http://www.cip.cc', timeout=5)
    str = re.findall(u'<div\s*class="data\s*kq-well">\s*<pre>(.+?)</pre>\s*</div>', respon.text, re.M | re.S | re.I)[0]
    REAL_CLIENT_ADDR = re.findall(u'数据三\s*:\s*(.+?)\n', str, re.M)[0]
    hzb = HZB()
    sleep_time= 5
    error_time= 1
    while True:
        try:
            hzb.scrapyAll()
            logger.info(u'本次检测处理已全部完成，%d分钟后进行下次检测处理。',sleep_time)
            time.sleep(60 * sleep_time)
        except Exception:
            logger.exception(u'刷课程序出现异常哦！%d分钟后将重新处理 ',error_time)
            time.sleep(60 * error_time)
