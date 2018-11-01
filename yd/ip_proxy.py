#!/usr/bin/python
#-*-coding:utf-8-*-

import time
import requests
import base64
from utils import Utils
import sys
reload(sys)
sys.setdefaultencoding('utf8')



class FeiyiProxy:
    # FEIYI_API = 'http://%s/open?user_name=%s&timestamp=%s&md5=%s&pattern=json&number=2&province=510000&city=                   '
    FEIYI_API = 'http://%s/open?user_name=%s&timestamp=%s&md5=%s&pattern=json&number=1'
    def __init__(self):
        self.__server = '183.129.207.77:88'
        self.__user_name = 'lycukgt86682'
        self.__password = '12345678'

    def __generateFeiyiApi(self):
        timestamp = int(time.time()*1000)
        md5 = Utils.getStrMD5('%s%s%s' %(self.__user_name,self.__password,timestamp))
        return self.FEIYI_API % (self.__server,self.__user_name,timestamp,md5)

    def getProxyIP(self):
        response = requests.get(self.__generateFeiyiApi())
        rs = response.json()
        print rs
        if rs['code'] == 100 :
            domain = rs['domain']
            port = rs['port']
            print domain,port
            return {'ip':domain,'port':port}


class WanDouProxy:
    WANDDOU_API = 'https://h.wandouip.com/get/ip-list?pack=0&num=1&xy=1&type=2&lb=\r\n&mr=1&'
    def __init__(self):
        self.__username = 'ming19871211@163.com'
        self.__password = 'Ming1211'
        self.__baseCode = None

    def __generateBaseCode(self):
        if self.__baseCode:
            return  self.__baseCode
        str = '%s:%s' % (self.__username, self.__password)
        encodestr = base64.b64encode(str.encode('utf-8'))
        self.__baseCode = ('Proxy-Authorization', 'Basic %s' % encodestr.decode())
        return self.__baseCode

    def getProxyIP(self):
        response = requests.get(self.WANDDOU_API)
        rs = response.json()
        if rs['code'] == 200:
            print rs['msg']
            for data in rs['data']:
                ip = data['ip']
                port = data['port']
                expire_time = data['expire_time']
                city = data['city']
                isp = data['isp']
                # print ip,port,expire_time,city,isp
                return {'ip': ip, 'port': port,'proxy-auth':self.__generateBaseCode()}


if __name__ == '__main__':
    feiyiProxy = FeiyiProxy()
    # feiyiPoxy.test()
    # print feiyiPoxy.getProxyIP()
    wandouProxy = WanDouProxy()
    wandouProxy.getProxyIP()
