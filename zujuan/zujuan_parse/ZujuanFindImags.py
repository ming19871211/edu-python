#!/usr/bin/python
#-*-coding:utf-8-*-

from utils.SqlUtil import PostgreSql
from utils import LoggerUtil
from cfg import COLL,PATH
import json
import os
import re
import sys
import urlparse
reload(sys)
sys.setdefaultencoding('utf-8')
logger = LoggerUtil.getLogger(__name__)

class ZujuanFindImags:
    def __init__(self):
        '''初始化配置数据'''
        self.SELECT_SQL = 'SELECT qid,old_id,seq,answer,analyses,content,options FROM T_QUES_ZUJUAN WHERE cate=1 AND subject= %s AND seq > %s ORDER BY seq ASC LIMIT %s '
        self.INSERT_SQL = 'INSERT into t_zujuan_img_url (qid,urls,status) values(%s,%s,%s)'
        self.UPDATE_SQL = 'UPDATE T_QUES_ZUJUAN set status = %s where qid = %s '
        self.ROWS = 1000

    def getZjImg(self,str):
        return re.findall(u'[\"|\'](https?://[a-z0-9A-z][a-z0-9A-z\.]+[a-z0-9A-z]/.*?)[\\\]?[\"|\']', str)

    def getFilename(self,url, root_path=PATH.rootImagPath):
        url_path = urlparse.urlsplit(url)
        return os.path.join(root_path, url_path.path[1:])

    def generateTmpImage(self, urls,tmp_suffix = PATH.tmp_suffix):
        for url in urls:
            url_file = self.getFilename(url)
            tmp_file = url_file + tmp_suffix
            dirname = os.path.dirname(url_file)
            if (not os.path.exists(url_file)) and (not os.path.exists(tmp_file)):
                if not os.path.exists(dirname): os.makedirs(dirname)
                with open(tmp_file, 'w+') as f:
                    f.write(url)

    def findImags(self,subject):
        seq_num = 0
        rows = self.ROWS
        try:
            pg = PostgreSql()
            flag = True
            count = 0
            while flag:
                try:
                    flag = False
                    insert_params = []
                    update_params = []
                    for row in pg.getAll(self.SELECT_SQL,(subject,seq_num,rows)):
                        flag =True
                        qid = row[0]
                        old_id = row[1]
                        seq_num = row[2]
                        try:
                            urls =[]
                            for col in row[3:]:
                                if col is None: continue
                                urls.extend(self.getZjImg(col))
                            print(urls)
                            # 生成临时的图片文件
                            self.generateTmpImage(urls)
                            # 插入数据到img表 存在图片状态为0，不存在图片状态为2
                            insert_params.append((qid, json.dumps(urls), 0 if urls else 2))
                            # 更新jyeoo主表的数据状态 存在图片状态修改为1，不存在图片状态为2
                            update_params.append((1 if urls else 2, qid))
                        except Exception as ex:
                            logger.exception(u"处理qi=%s，old_id=%s，创建题目的图片发生异常,异常信息：%s" % (qid, old_id,ex.message))
                    if update_params: pg.batchExecute(self.UPDATE_SQL, update_params)
                    if insert_params: pg.batchExecute(self.INSERT_SQL, insert_params)
                    pg.commit()
                    count += len(update_params)
                    logger.info(u'已成功处理题目数量:%d' % count)
                except Exception as e:
                    pg.rollback()
                    logger.exception("批量处理-异常信息:%s" %(e.message))
        finally:
            pg.close()




if __name__ == '__main__':
    findImages = ZujuanFindImags()
    findImages.findImags(16)
    findImages.findImags(17)

