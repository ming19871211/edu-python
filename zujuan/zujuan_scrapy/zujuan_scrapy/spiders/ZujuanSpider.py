#!/usr/bin/python
#-*-coding:utf-8-*-

import scrapy
#import os
import json
from zujuan_scrapy.settings import rootUrl,knowledUrl,curr_subject,COLL
from zujuan_scrapy.Utils import MongoDB
from zujuan_scrapy.items import QuestionPgItem
import sys
reload(sys)
sys.setdefaultencoding('utf8')


class ZujuanKnowledQuestionSpider(scrapy.Spider):
    name="zujuan_knowled_question"

    def start_requests(self):
        yield scrapy.Request(url=rootUrl,meta={'cookiejar': 1},callback=self.parse)

    def parse(self, response):
        url = knowledUrl % (curr_subject['chid'], curr_subject['xd'])
        yield scrapy.Request(url,meta={'cookiejar': response.meta['cookiejar']},
                              callback=self.subjectParse)

    def subjectParse(self,response):
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.pg_url)
        cursor = coll.find({'cid':curr_subject['subjectCode'],'status':{'$exists':False}})
        for doc in cursor:
            yield scrapy.Request(doc['url'], meta={'cookiejar': response.meta['cookiejar'],'doc':doc},
                           callback=self.pgParse)

    def pgParse(self,response):
        item = QuestionPgItem()
        item['doc'] = response.meta['doc']
        rs = json.loads(response.body_as_unicode())
        if rs['total'] and len(rs['data'][0]['questions']) == item['doc']['rows']:
            item['questions'] = rs
        else:
            self.logger.error('下载pg页面异常,url:%s',response.url)
            raise ValueError('下载pg页面异常,url:%s' % response.url)
        return item
