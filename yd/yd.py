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
from ConfigParser import ConfigParser
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
html_parser = HTMLParser.HTMLParser()
logger = LoggerUtil.getLogger(__name__)
SELECT_SQL = "select id,generate_url,course_id,class_room_id,user_name,user_id,user_mobile,play_time from t_hzb_course WHERE state='%s'  and start_time<= now() and end_time >= now() limit %s"

#读取配置文件
cfg = ConfigParser()
cfg.read('yd.cfg')
SECTION_TYPE = "yd"
def getCFG(option,defalut): return cfg.get(SECTION_TYPE,option) if cfg.has_option(SECTION_TYPE,option) else defalut
#并发数量
CONCURRENT_NUMBER =  int(getCFG('CONCURRENT_NUMBER',10))

class YD:
    def __init__(self):
        path_str = os.getenv('path')
        pwd_str = os.getcwd()
        if path_str.find(pwd_str) == -1:
            sys.path.append(pwd_str)

    def scrapyAll(self,select_sql=SELECT_SQL,thread_num=CONCURRENT_NUMBER):
        count = 1
        total = 0
        while count:
            count = 0
            mysql = Mysql()
            try:
                for rs in  mysql.getAll(select_sql,(0,thread_num)):
                    count += 1
                    id, generate_url, course_id, class_room_id, user_name, user_id, user_mobile, play_time = rs
                    try:
                        sql = "update t_hzb_course set state=%s,modify_time=now() WHERE id=%s and user_id=%s"
                        mysql.execute(sql, (1, id, user_id))
                        mysql.commit()
                    except Exception:
                        mysql.rollback()
                        logger.exception(u'修改数据状态异常！')
                    YDThread(rs).start()
            finally:
                mysql.close()
            for t in threading.enumerate():
                if t is threading.currentThread():
                    continue
                t.join()
            total += count
            logger.info(u'已处理访问数量%d',total)

class YDThread(threading.Thread):
    def __init__(self,rs):
        threading.Thread.__init__(self)
        self.rs = rs

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
        driver = self.__startChrome()
        try:
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
            while isNotPlay:
                logger.info(u'%s-%s,等待下载中...%s',user_name,user_mobile,playBtn.get_attribute('class'))
                isNotPlay =  "play_btn gs-icon-pause" != playBtn.get_attribute('class')
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
                sql = "update t_hzb_course set state=%s,real_play_time=%s,modify_time=now() WHERE id=%s and user_id=%s"
                mysql.execute(sql,(2,real_play_time,id,user_id))
                mysql.commit()
            except Exception:
                mysql.rollback()
                logger.exception(u'观看视频完成更新时异常')
            finally:
                mysql.close()
        except Exception:
            logger.exception(u'视频播放出现问题！')
        finally:
            pass
            self.__closeChrome(driver)

if __name__ == '__main__':
    yd = YD()
    while True:
        try:
            yd.scrapyAll()
        except Exception:
            logger.exception(u'爬虫出现异常哦！')
        time.sleep(60*30)