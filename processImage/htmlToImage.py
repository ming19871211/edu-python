#!/usr/bin/python
#-*-coding:utf-8-*-

import sys
import os
from utils import Utils,LoggerUtil
from utils.SqlUtil import PostgreSql
reload(sys)
sys.setdefaultencoding('utf8')

logger = LoggerUtil.getLogger(__name__)

def jyeooAnalysisToPic():
    postgresql = PostgreSql()
    try:
        qid = ' '
        rows = 1000
        page = 0
        flag = True # 是否存在数据
        sql = 'SELECT qid FROM "public"."t_ques_jyeoo" where seq > %s and seq <= %s'
        base_url = 'http:/10.200.150.2:20017/ques/analyseById?qid=%s'
        base_app_url = 'http://10.200.150.2:20017/ques/app/analyseById?qid=%s'
        root_path = 'picture'
        if not os.path.exists(root_path): os.makedirs(root_path)
        count = 0 # 处理数据
        while flag:
            flag = False
            page += 1
            for row in postgresql.getAll(sql,(rows * (page-1),rows * page)):
                qid = row[0]
                flag = True
                count += 1
                #生成web图片
                url = base_url % qid
                pic_name = qid + '.png'
                pic_file = os.path.join(root_path,pic_name)
                if not os.path.exists(pic_file):
                    Utils.htmlToImages(url,pic_file,605)
                #生成app图片
                app_url = base_app_url % qid
                pic_app_name = qid + '.app.png'
                pic_app_file = os.path.join(root_path, pic_app_name)
                if not os.path.exists(pic_app_file):
                    Utils.htmlToImages(app_url, pic_app_file,306)
            logger.info(u'已处理菁优图片数量%d',count)
    finally:
        postgresql.close()

if __name__ == '__main__':
    jyeooAnalysisToPic()


import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
def htmlToPicBywebDriver():
    '''仅作为研究用'''
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.customHeaders.User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.91 Safari/537.36"
    driver = webdriver.PhantomJS(desired_capabilities=dcap)
    driver.set_window_size(0, 0)
    driver.implicitly_wait(3)
    driver.get("http://127.0.0.1:20017/ques/analyseById?qid=00a0a7c4-8fe2-414f-8e08-9f06f91c838a")
    time.sleep(1)
    print driver
    html = driver.current_url
    print driver.get_window_size()
    with open('a.png','wb') as f: f.write(driver.get_screenshot_as_png())
    driver.get("http://127.0.0.1:20017/ques/analyseById?qid=218a6387-cfb2-46b7-8732-b3b03212a20f")
    with open('b.png', 'wb') as f: f.write(driver.get_screenshot_as_png())








