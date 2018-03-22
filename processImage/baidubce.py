#!/usr/bin/python
#-*-coding:utf-8-*-

import json
import urllib, urllib2
import base64
import sys
import time
reload(sys)
sys.setdefaultencoding('utf-8')
#【官网获取的AK】
default_client_id = 'Xm0mGeDtvpwkUNtGlrnIBn08'
#【官网获取的SK】
default_client_secret = 'GOnnMz3HiCNe70rnfL9sOaN4AKMNFj3p'
default_host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s'

def getAccessToken(client_id=default_client_id,client_secret=default_client_secret,base_host=default_host):
    host = base_host % (client_id,client_secret)
    request = urllib2.Request(host)
    request.add_header('Content-Type', 'application/json; charset=UTF-8')
    response = urllib2.urlopen(request)
    content = response.read()
    if (content):
        return json.loads(content)
    else:
        return None
def get_img_base64(img_file):
    with open(img_file, 'rb') as infile:
        s = infile.read()
        return base64.b64encode(s)
def getRequestId(img_file,access_token,ocr_url='https://aip.baidubce.com/rest/2.0/solution/v1/form_ocr/request'):
    request = urllib2.Request(ocr_url)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    data = {}
    data['access_token'] = access_token
    data['image'] = get_img_base64(img_file)
    response = urllib2.urlopen(request,data= urllib.urlencode(data))
    return json.loads(response.read())

def getContent(access_token,request_id,ocr_url='https://aip.baidubce.com/rest/2.0/solution/v1/form_ocr/get_request_result'):
    request = urllib2.Request(ocr_url)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    data = {}
    data['access_token'] = access_token
    data['request_id'] = request_id
    data['result_type'] = 'excel'
    response = urllib2.urlopen(request, data=urllib.urlencode(data))
    return response.read()


APP_ID='10910725'
API_KEY = 'Xm0mGeDtvpwkUNtGlrnIBn08'
SECRET_KEY = 'GOnnMz3HiCNe70rnfL9sOaN4AKMNFj3p'
from aip import AipOcr
def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()
def sendImg(aipOcr,img_file,img_file_pre):
    rs = aipOcr.tableRecognitionAsync(get_file_content(img_file))
    print rs
    # {u'log_id': 152081725536032L, u'result': [{u'request_id': u'10910725_196056'}]}
    with open(img_file_pre + 'request_id.txt', 'w') as f:  f.write(json.dumps(rs))
    return rs
def getRs(aipOcr,request_id,img_file_pre):
    rs2 = aipOcr.getTableRecognitionResult(request_id, { 'result_type': 'json',})
    print rs2
    with open(img_file_pre + '.baidu.json', 'w') as f:  f.write(json.dumps(rs2, ensure_ascii=False))
    return rs2


if __name__ == '__main__':
    img_file = 'data/pipi_b.jpg'

    # img_file_pre = img_file.split('.')[0]
    # aipOcr = AipOcr(APP_ID,API_KEY,SECRET_KEY)
    # rs = sendImg(aipOcr,img_file,img_file_pre)
    # time.sleep(30)
    # request_id = rs['result'][0]['request_id']
    # rs2 = getRs(aipOcr,request_id,img_file_pre)


    access_token = getAccessToken()
    rs_s = getRequestId(img_file,access_token)
    request_id =  rs_s['result'][0]['request_id']
    print request_id
    time.sleep(30)
    text = getContent(access_token,request_id)
    print text

    ##
    # 10910725_196249
    # {"result": {
    #     "result_data": "http://bj.bcebos.com/v1/aip-web/form_ocr/E9C64668EB1E42AC984CCE314AC90A7F.xls?authorization=bce-auth-v1%2Ff86a2044998643b5abc89b59158bad6d%2F2018-03-12T02%3A41%3A10Z%2F86400%2F%2Ff16653f3bfa6dd96d3e2566102f263b0f98bc39656ef5fa336fe95683a34a9a6",
    #     "ret_msg": "已完成", "request_id": "10910725_196249", "percent": 100, "ret_code": 3}, "log_id": 152082249070984}

    # 10910725_196269
    # {"result": {
    #     "result_data": "http://bj.bcebos.com/v1/aip-web/form_ocr/A793D4BC40C040218E5074C851352763.xls?authorization=bce-auth-v1%2Ff86a2044998643b5abc89b59158bad6d%2F2018-03-12T02%3A45%3A27Z%2F86400%2F%2Fff81f8b9b6fde6c9581fd369c2eea3f660424040f314c42cb5b748e6fb636ee2",
    #     "ret_msg": "已完成", "request_id": "10910725_196269", "percent": 100, "ret_code": 3}, "log_id": 152082274090320}

    # 10910725_197502
    # {"result": {
    #     "result_data": "http://bj.bcebos.com/v1/aip-web/form_ocr/B67E6896455843DDACB75C4E64B03120.xls?authorization=bce-auth-v1%2Ff86a2044998643b5abc89b59158bad6d%2F2018-03-13T01%3A33%3A05Z%2F86400%2F%2Fc44d99fe73489ae27aeaec9bac11c0b92faca3a36a4cf6f39fca339dab5d2b8c",
    #     "ret_msg": "已完成", "request_id": "10910725_197502", "percent": 100, "ret_code": 3}, "log_id": 152090479515963}

