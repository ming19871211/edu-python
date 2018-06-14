#!/usr/bin/python
#-*-coding:utf-8-*-

from utils.SqlUtil import MongoDB,PostgreSql
from cfg import COLL
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def exportKnowledToPg(mongon,pg):
    sql = 'insert into zujuan_point(id,name) VALUES (%s,%s)'
    coll = mongon.getCollection(COLL.knowled)
    params = []
    total = 0
    count = 0
    for doc in coll.find():
        id = doc['id']
        title = doc['title']
        params.append((id,title))
        total += 1
        if len(params) >= 1000:
            try:
                pg.batchExecute(sql,params)
                pg.commit()
                count += len(params)
                params = []
            except Exception as e:
                pg.rollback()
                print(e.message)
            print u'处理总数：%d，成功处理数量: %d' % (total,count)
    if params:
        try:
            pg.batchExecute(sql, params)
            pg.commit()
            count += len(params)
        except Exception as e:
            pg.rollback()
            print(e.message)
        print u'处理总数：%d，成功处理数量: %d' % (total, count)





if __name__ == '__main__':
    mongon = MongoDB()
    pg = PostgreSql()
    try:
        exportKnowledToPg(mongon,pg)
    finally:
        pg.close()
        mongon.close()






