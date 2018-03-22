#!/usr/bin/python
#-*-coding:utf-8-*-

import sys
import os
from utils import Utils,LoggerUtil
from utils.SqlUtil import PostgreSql
import shutil
reload(sys)
sys.setdefaultencoding('utf8')

logger = LoggerUtil.getLogger(__name__)

def processImage():
    # 初始化
    root_path = 'picture'
    analysis_path = 'analysis'
    if not os.path.exists(root_path): os.makedirs(root_path)
    if not os.path.exists(analysis_path): os.makedirs(analysis_path)
    postgresql = PostgreSql()
    try:
        num_id = 0
        rows = 1000
        sql = 'SELECT id,old_id,new_id FROM "public"."t_ques_id" where id > %s and status = 0 order by id ASC limit %s'
        update_sql = 'UPDATE t_ques_id SET status = 1,analysis_url= %s WHERE old_id = %s'
        count = 0  # 处理数据
        total = 0
        flag = True  # 是否存在数据
        while flag:
            flag = False
            update_params = []
            for row in postgresql.getAll(sql, (num_id, rows)):
                num_id = row[0]
                flag = True
                old_id = row[1]
                new_id = row[2]
                total += 1
                pic_file = os.path.join(root_path, old_id + '.png')
                pic_app_file = os.path.join(root_path, old_id + '.app.png')
                if os.path.exists(pic_file) and os.path.exists(pic_app_file) and os.path.getsize(pic_app_file) > 0 and os.path.getsize(pic_file) > 0:
                    new_file = new_id + '.png'
                    pic_new_file = os.path.join(analysis_path, new_file)
                    pic_new_app_file = os.path.join(analysis_path, new_id + '.app.png')
                    shutil.copyfile(pic_file,pic_new_file)
                    shutil.copyfile(pic_app_file,pic_new_app_file)
                    analysis_url = 'http://image.yuncelian.com/1/analysis/'+new_file
                    update_params.append((analysis_url,old_id))
                    count += 1
            if update_params: postgresql.batchExecute(update_sql,update_params)
            postgresql.commit()
            logger.info(u'处理总数：%d,已处理菁优图片数量：%d',total,count)
    finally:
        postgresql.close()

if __name__ == '__main__':
    processImage()
