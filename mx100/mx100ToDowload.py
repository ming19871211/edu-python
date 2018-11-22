#!/usr/bin/python
#-*-coding:utf-8-*-


from utils import LoggerUtil
import urlparse
import requests
import threading
import Queue
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

ROOT_PATH= 'resource'
TMP_SUFFIX = '-tmp'
THREAD_MAX_NUM=20
q = Queue.Queue(30)
logger = LoggerUtil.getLogger(__name__)
class MX100ToDowload(object):
    def __init__(self):
        pass
    def __getFilename(self,url, root_path=ROOT_PATH):
        url_path = urlparse.urlsplit(url)
        return os.path.join(root_path, url_path.path[1:])

    def generateTmp(self,fileName='media-url.txt',tmp_suffix=TMP_SUFFIX):
        total = 0
        with open(fileName,'r') as file:
            while True:
                url = file.readline()
                if not url: break
                #生成文件
                url=url.rstrip('\n').rstrip('\r')
                url_file = self.__getFilename(url)
                tmp_file = url_file+tmp_suffix
                dirname = os.path.dirname(url_file)
                if (not os.path.exists(url_file)) and (not os.path.exists(tmp_file)):
                    if not os.path.exists(dirname): os.makedirs(dirname)
                    with open(tmp_file, 'w+') as f: f.write(url)
                total +=1
                if total%1000 == 0:
                    logger.info(u'处理进度，处理总数：%s', total)
        if total % 1000:
            logger.info(u'处理进度，处理总数：%s', total)

    def dowloadFile(self,root_path=ROOT_PATH,tmp_suffix=TMP_SUFFIX):
        for i in range(0,THREAD_MAX_NUM):
            DowloadThread().start()
        proccess_num = 0
        for parent,dir_names,file_names in os.walk(root_path):
            for file_name in file_names:
                if file_name.endswith(tmp_suffix):
                    file_t_name = os.path.join(parent,file_name)
                    file_r_name = file_t_name.rstrip(tmp_suffix)
                    with open(file_t_name,'r') as f:
                        url = f.read()
                    q.put((url,file_t_name,file_r_name))
                    proccess_num += 1
                    if proccess_num % 1000 == 0:
                        logger.info(u'处理进度，处理总数：%s', proccess_num)
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue
            t.join()
        if proccess_num % 1000:
            logger.info(u'处理进度，处理总数：%s', proccess_num)

class DowloadThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            try:
                try:
                    url,file_t_name,file_r_name=q.get(timeout=10)
                except Exception:
                    break
                response = requests.get(url)
                if response.status_code == 200:
                    with open(file_r_name, 'wb') as f1: f1.write(response.content)
                    os.remove(file_t_name)
            except Exception as e:
                logger.exception(u'下载文件异常,url:%s, 临时文件:%s, 正式文件：%s',url,file_t_name,file_r_name)


if __name__ == '__main__':
    mx = MX100ToDowload()
    # mx.generateTmp()
    mx.dowloadFile()