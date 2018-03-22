# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import items
from Utils import MongoDB
from settings import COLL
import json

mongo = MongoDB()
coll_pg = mongo.getCollection(COLL.pg_url)
coll_question = mongo.getCollection(COLL.question)
class ZujuanScrapyPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item,items.QuestionPgItem):
            coll_pg.update_one({'kid': item['doc']['kid'],'pg':item['doc']['pg']},
                            {"$set": {"pgdata": item['questions'], 'status': 1},
                             "$currentDate": {"lastModified": True}})
        elif isinstance(item,items.QuestionTtem):
            question = item['question']
            coll_question.update_one({'question_id':question['question_id']},
                                     {'$set':{'new_data':question,'status':item['status']},
                                      "$currentDate": {"lastModified": True}})
        return item
