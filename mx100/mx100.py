#!/usr/bin/python
#-*-coding:utf-8-*-


from utils import LoggerUtil
from utils.SqlUtil import Oracle
import urllib2
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
SELECT_SQL = u"select * FROM (select id,path,status,filesize FROM T_ESR_RESOURCE where id > :id and  STATUS in('02','03') order by id asc)  where  ROWNUM  <= :num"
UPDATE_SQL = u"update T_ESR_RESOURCE set  FILESIZE=:filesize where id=:id"
NUM=1000
logger = LoggerUtil.getLogger(__name__)
class MX100(object):
    def __init__(self):
        pass

    def getFileSize(self,url, proxy=None):
        """通过content-length头获取文件大小
        url - 目标文件URL
        proxy - 代理
        """
        if not url:return None
        opener = urllib2.build_opener()
        if proxy:
            if url.lower().startswith('https://'):
                opener.add_handler(urllib2.ProxyHandler({'https': proxy}))
            else:
                opener.add_handler(urllib2.ProxyHandler({'http': proxy}))
        request = urllib2.Request(url)
        request.get_method = lambda: 'HEAD'
        try:
            response = opener.open(request)
            response.read()
        except Exception, e:
            print '%s %s' % (url, e)
        else:
            return dict(response.headers).get('content-length', 0)
    def analysis(self,select_sql=SELECT_SQL,update_sql=UPDATE_SQL,num=NUM):
        orc = Oracle()
        try:
            total = 0
            each_total=1
            succ_count = 0
            err_count=0
            id = 0
            while each_total:
                each_succ_count = 0
                each_total = 0
                param = {'num':num,'id':id}
                rs = orc.getAll(select_sql,param)
                update_params = []
                for row in rs:
                    each_total +=1
                    total +=1
                    new_id, url, status,f_size = row
                    if id >= new_id:
                        raise Exception(u'SQL查询出现了问题哦')
                    id = new_id
                    if url and not url.startswith('http'):
                        url = u'http://media.mx100.cn/zhw/%s' % url
                    if  not f_size and f_size != 0:
                        fileSize = self.getFileSize(url)
                        if not fileSize:
                            fileSize = 0
                        else:
                            fileSize = int(fileSize)
                        update_params.append({'filesize':fileSize,'id':id})
                if update_params:
                    try:
                        orc.batchExecute(update_sql,update_params)
                        orc.commit()
                        succ_count += len(update_params)
                        logger.info(u'本次成功提交数量:%s',len(update_params))
                    except Exception:
                        err_count += len(update_params)
                        orc.cancel()
                        logger.exception(u'批量执行sql异常，本次总数：%s,异常数量:%s' ,each_total,len(update_params))
                logger.info(u'处理进度，处理总数：%s,成功处理数量：%s，数据批量操作异常数量：%s',total,succ_count,err_count)
        except Exception as e:
            logger.exception(u'数据异常')
            raise  e
        finally:
            orc.close()


if __name__ == '__main__':

    mx = MX100()
    mx.analysis()