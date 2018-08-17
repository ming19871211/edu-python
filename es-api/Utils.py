#!/usr/bin/python
#-*-coding:utf-8-*-

import sys
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import json
import hashlib
import pickle
import time
import logging
import logging.config
reload(sys)
sys.setdefaultencoding('utf-8')
# 加载日志配置文件
logging.basicConfig(level=logging.INFO,format = '[%(asctime)s - %(filename)s- %(levelname)s] - %(message)s',
                    filename='es.log')
def getLogger(name=None):
    '''返回日志对象'''
    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger

class Email():
    '''邮件对象'''
    def __init__(self,email_host='smtp.139.com',email_port=25,login_user='ming19871211@139.com',login_passwd='ming1234'):
        self.__email_host = email_host
        self.__email_port = email_port
        self.__login_user = login_user
        self.__login_passwd = login_passwd
    def sendmail(self,message,to_addrs='meiqiming@talkweb.com.cn',topic=u'Elasticsearch logs Exception',topic_tpye='plain'):
        if not isinstance(message,basestring):
            raise Exception(u'必须是字符串类型')
        smtp = smtplib.SMTP()
        code = None
        try:
            msg = MIMEText(message,topic_tpye, 'utf-8')
            msg['Subject'] =Header(topic,'utf-8').encode()
            msg['From'] = u'%s' % self.__login_user
            if isinstance(to_addrs,list):
                msg['To'] = ",".join(to_addrs)
            else:
                msg['To'] =  u'%s' % to_addrs
            code, text = smtp.connect(self.__email_host,self.__email_port)
            code_erro = 0
            while code != 220 and code_erro < 3:
                time.sleep(3)
                code_erro += 1
                code, text = smtp.connect(self.__email_host, self.__email_port)
            smtp.login(self.__login_user,self.__login_passwd)
            smtp.sendmail(self.__login_user, to_addrs, msg.as_string())
        finally:
            if code and code == 220:
                smtp.quit()
                smtp.close()
def getMD5(obj):
    '''获取字符串的MD5码'''
    if not isinstance(obj,basestring):
        obj = toJson(obj)
    hashmd5 = hashlib.md5()
    hashmd5.update(obj)
    return hashmd5.hexdigest()

def toJson(list):
    '''转换为json格式'''
    return json.dumps(list,ensure_ascii=False)

def datetime_toString(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def getCurrMilliSecond():
    return long(time.time()*1000)


__file_pkl_name="es.pkl"

def saveCache(key,value,expired_time):
    try:
        es_dic = pickle.load(open(__file_pkl_name, "rb"))
    except Exception:
        es_dic = {}
    es_dic[key]=[value,time.time(),expired_time]
    pickle.dump(es_dic, open(__file_pkl_name, "wb"))

def hasCache(key):
    try:
        es_dic = pickle.load(open(__file_pkl_name, "rb"))
    except Exception:
        es_dic = {}
    if es_dic.has_key(key):
        value, save_time, expired_time = es_dic[key]
        if time.time()-es_dic[key][1] < expired_time*60:
            return True
    return False
