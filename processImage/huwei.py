#!/usr/bin/python
#-*-coding:utf-8-*-

import json
import urllib, urllib2
import requests
import base64
import sys
import time
reload(sys)
sys.setdefaultencoding('utf-8')

USER_NAME = u'zhangshujing'
PASSWORD = u'Talkweb_2018'
ACCOUNT_NAME = u'zhangshujing'
TOKEN_URL =u'https://iam.cn-north-1.myhuaweicloud.com/v3/auth/tokens'
OCR_TABLE_URL=u'https://ais.cn-north-1.myhuaweicloud.com/v1.0/ocr/general-table'

def getToken(username=USER_NAME,password=PASSWORD,accountname=ACCOUNT_NAME,token_url=TOKEN_URL):
    request = urllib2.Request(token_url)
    request.add_header('Content-Type', 'application/json')
    data = {"auth": {
        "identity": {"methods": ["password"],
                     "password": {"user": {"name": username, "password": password,
                                           "domain": {"name": accountname}}}},
        "scope": {"project": {"name": "cn-north-1"}}
    }}
    response = urllib2.urlopen(request,data=json.dumps(data))
    return response.headers['X-Subject-Token']

def getOcrTable(token,img_file,url=OCR_TABLE_URL):
    request = urllib2.Request(url)
    request.add_header('Content-Type', 'application/json')
    request.add_header('X-Auth-Token',token)
    data ={
        'image':get_img_base64(img_file),
        'url':''
    }
    response = urllib2.urlopen(request, data=json.dumps(data))
    return response.read()
def get_img_base64(img_file):
    with open(img_file, 'rb') as infile:
        s = infile.read()
        return base64.b64encode(s)
if __name__ == '__main__':
    token = getToken()
    print token
    img_file = 'data/pipi_b.jpg'
    rs = getOcrTable(token,img_file)
    with open(img_file + '.huawei.json', 'w') as f:  f.write(json.dumps(rs))
    print rs