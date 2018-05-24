#!/usr/bin/python
#-*-coding:utf-8-*-

from utils.SqlUtil import MongoDB,PostgreSql
from utils import LoggerUtil
from cfg import COLL
import json
import sys
import uuid
reload(sys)
sys.setdefaultencoding('utf-8')
logger = LoggerUtil.getLogger(__name__)

class ZujuanQuestion:
    def __init__(self):
        '''初始化配置数据'''
        self.insert_sql = 'insert into t_ques_zujuan(qid,answer,analyses,cate,cate_name,content,options,points,subject,difficulty,status,provider,old_id ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'

    def paresToPg(self,cid):
        mg = MongoDB()
        pg = PostgreSql()
        try:
            coll = mg.getCollection(COLL.question)
            # 获取题型
            type_dic = {}
            for row in pg.getAll('SELECT code,name,zujuan_code,zujuan_name FROM t_ques_type_zujuan_relation where subject_code = %s',(cid,)):
                type_dic[str(row[2])] = {'code': row[0], 'name': row[1]}
            insert_params = []
            self.total = 0
            self.count = 0
            for doc in coll.find({'cid':cid,'status':{'$in':[0,1]}}):
                try:
                    self.total += 1
                    old_id = doc['question_id'] #题目原始id
                    qid = str(uuid.uuid1()) # 新的题目Id
                    difficulty = doc['new_data']['difficult_index']  # 难度
                    subject = cid #课程ID
                    provider = '04' # 来源
                    status = 0 #状态
                    # 最后一级知识点集合
                    points = []
                    for kid_dic in doc['kids']:
                        points.append({'code':kid_dic['kid'],'name':kid_dic['ktitle']})
                    points = json.dumps(points)
                    # 题目类型处理
                    question_channel_type = doc['new_data']['question_channel_type']
                    cate = type_dic[question_channel_type]['code']
                    cate_name = type_dic[question_channel_type]['name']

                    # 题干、答案
                    content = doc['new_data']['question_text']
                    answer = []
                    if doc['new_data'].has_key('list') and doc['new_data']['list']:
                        for childe_content in  doc['new_data']['list']:
                            content = '%s <br/> %s' %(content,childe_content['question_text'])
                            if not childe_content['answer']:
                                coll.update_one({'question_id': old_id},
                                                {'$set': {'status': None},
                                                 "$currentDate": {"lastModified": True}})
                                raise Exception('题目答案异常，id:%s' % old_id)
                            answer.append('<img align="top" src="%s" />' % childe_content['answer'])
                            if childe_content['options']:
                                content = '%s <br/> %s' % (content, json.dumps( childe_content['options'],ensure_ascii=False))
                    else:
                        if not doc['new_data']['answer']:
                            coll.update_one({'question_id': old_id},
                                            {'$set': {'status': None},
                                             "$currentDate": {"lastModified": True}})
                            raise Exception('题目答案异常，id:%s' % old_id)
                        answer.append('<img align="top" src="%s" />' % doc['new_data']['answer'])
                    answer = json.dumps(answer,ensure_ascii=False)

                    #题目选项处理
                    options = []
                    if question_channel_type in ['1','2']:
                        if isinstance(doc['new_data']['options'], unicode):
                            #选择题没有选项的状态,变为-1
                            coll.update_one({'question_id': old_id},
                                            {'$set': {'status': -1}, "$currentDate": {"lastModified": True}})
                        for key,value in doc['new_data']['options'].items():
                            options.insert(ord(key)-ord('A'),value)
                    options = json.dumps(options,ensure_ascii=False)
                    analyses = doc['new_data']['explanation'] if doc['status'] == 1 else None  #解析
                    if analyses:
                        analyses = '< img align="top" src="%s" />' % analyses
                    insert_params.append((qid,answer,analyses,cate,cate_name,content,options,points,subject,difficulty,status,provider,old_id))
                except Exception as e:
                    logger.exception(u'处理分析组卷题目失败，题目id-%s',old_id)
                if len(insert_params)>= 1000:
                    count = self.batchInsertExecute(pg,insert_params)
                    insert_params = []
            self.batchInsertExecute(pg,insert_params)
        finally:
            mg.close()
            pg.close()

    def batchInsertExecute(self,pg,insert_params):
        if insert_params:
            try:
                pg.batchExecute(self.insert_sql, insert_params)
                pg.commit()
                self.count +=len(insert_params)
                logger.info(u'已处理题目总数：%d，成处理题目数量：%d',self.total,self.count)
            except Exception as e:
                pg.rollback()
                logger.exception(u'批量插入组卷题目数量异常，题目数量:%d',len(insert_params))


if __name__ == '__main__':
    question = ZujuanQuestion()
    question.paresToPg(16)
