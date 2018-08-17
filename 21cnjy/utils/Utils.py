#!/usr/bin/env python
# -*- coding:utf-8 -*-

from PIL import Image
import hashlib
import os
import sys
import urlparse
import uuid
import socket
import smtplib
import json
from email.mime.text import MIMEText
from email.header import Header
import time

reload(sys)
sys.setdefaultencoding('utf-8')

class Email():
    '''邮件对象'''
    def __init__(self,email_host='smtp.139.com',email_port=25,login_user='ming19871211@139.com',login_passwd='ming1234'):
        self.__email_host = email_host
        self.__email_port = email_port
        self.__login_user = login_user
        self.__login_passwd = login_passwd
    def sendmail(self,to_addrs,message,topic=u'jeyoo crawl exception',topic_tpye='plain'):
        smtp = smtplib.SMTP()
        # smtp.set_debuglevel(1)
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

def dhash(imageFileName, hash_size = 8):
    '''得到图片的相识度MD5值'''
    # Grayscale and shrink the image in one step.
    image = Image.open(imageFileName)
    image = image.convert('L').resize((hash_size + 1, hash_size),Image.ANTIALIAS,)
    pixels = list(image.getdata())
    # Compare adjacent pixels.
    difference = []
    for row in xrange(hash_size):
        for col in xrange(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)
    # Convert the binary array to a hexadecimal string.
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2**(index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0
    return ''.join(hex_string)

def modifyMD5(fileName):
    '''修改文件的MD5值'''
    with open(fileName,'ab') as f: f.write("####&&&&")

def getFilename(url,root_path):
    '''获取url下载保存的文件全名“包含路径”'''
    url_path = urlparse.urlsplit(url)      
    return os.path.join(root_path,url_path.path[1:])

def getStrMD5(s):
    '''获取字符串的MD5码'''
    hashmd5 = hashlib.md5()
    hashmd5.update(s)
    return hashmd5.hexdigest()

def getFileMD5(fileName):
    '''获取文件的MD5码'''
    hashmd5 = hashlib.md5()
    with open(fileName,'rb') as f:hashmd5.update(f.read())
    return hashmd5.hexdigest()
def getBigFileMD5(fileName):
    '''获取大文件的MD5码'''
    hashmd5 = hashlib.md5()
    with open(fileName,'rb') as f:
        while True:
            b = f.read(8096)
            if not b : break
            hashmd5.update(b)
    return hashmd5.hexdigest()

def getMacAddress():
    '''获取本机MAC（物理）地址'''
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

def getHostName():
    '''获取本机电脑名'''
    return socket.getfqdn(socket.gethostname(  ))

def getIpAddr(hostname):
    '''获取指定电脑名称的IP地址'''
    return socket.gethostbyname(hostname)

#全局参数
webkit_cmd = 'webkit2png  -W  -o %s  -w 1  -g 0 0 -x %d %d %s'
default_width = 605
default_height = 30
def htmlToImages(url,pic_name,width=default_width,height=default_height,cmd=webkit_cmd):
    '''网页转换为图片'''
    width = round(1.5 * width)  # 默认放大了1.5
    os.system(cmd % (pic_name+'-tmp',width,height,url))
    img = Image.open(pic_name+'-tmp')
    #width = img.size[0] #不能以图片的宽度为依据，图片宽度会需要加上边框才是实际的宽度
    height = img.size[1]
    os.remove(pic_name+'-tmp')
    os.system(cmd % (pic_name, width, height, url))
    return pic_name

def toJson(list):
    '''转换为json格式'''
    return json.dumps(list,ensure_ascii=False)

def datetime_toString(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def getCurrMilliSecond():
    return long(time.time()*1000)