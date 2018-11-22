#!/usr/bin/python
#-*-coding:utf-8-*-


from utils import LoggerUtil
from utils.SqlUtil import Oracle
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
SELECT_SQL = u"select * FROM (select id,path,status,filesize FROM T_ESR_RESOURCE where id > :id and filesize > 0  and STATUS in('02','03') order by id asc)  where  ROWNUM  <= :num"
NUM=1000
logger = LoggerUtil.getLogger(__name__)
class MX100ToURL(object):
    def __init__(self):
        pass

    def __addUrl(self,url,fileName=None):
        fileName = fileName if fileName else 'url.txt'
        with open(fileName,'a') as file:
            file.write(url+'\n')

    def analysis(self,select_sql=SELECT_SQL,num=NUM):
        orc = Oracle()
        try:
            total = 0
            each_total=1
            id = 0
            while each_total:
                each_total = 0
                param = {'num':num,'id':id}
                rs = orc.getAll(select_sql,param)
                for row in rs:
                    each_total +=1
                    total +=1
                    new_id, url, status,filesize = row
                    if id >= new_id:
                        raise Exception(u'SQL查询出现了问题哦')
                    id = new_id
                    if url and not url.startswith('http'):
                        url = u'http://media.mx100.cn/zhw/%s' % url

                    if url.startswith('http://file.cjxxpt.com'):
                        self.__addUrl(url,'file-url.txt')
                    elif url.startswith('http://media'):
                        self.__addUrl(url,'media-url.txt')
                    else:
                        self.__addUrl(url,'other-url.txt')


                logger.info(u'处理进度，处理总数：%s',total)
        except Exception as e:
            logger.exception(u'数据异常')
            raise  e
        finally:
            orc.close()


if __name__ == '__main__':
    mx = MX100ToURL()
    mx.analysis()