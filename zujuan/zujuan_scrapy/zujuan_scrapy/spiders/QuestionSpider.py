#!/usr/bin/python
#-*-coding:utf-8-*-

import scrapy
import json
import re
from zujuan_scrapy.settings import COLL
from zujuan_scrapy.Utils import MongoDB
from zujuan_scrapy.items import QuestionTtem

login_index_url = 'http://passport.zujuan.com/login'
login_url = 'http://passport.zujuan.com/login?jump_url='
question_url = 'http://www.zujuan.com/question/detail-%s.shtml'

username = '18175183893'
password = 'ming1234'
subjectcode = 23


class QuestionSpider(scrapy.Spider):
    name="zujuan_question"

    def start_requests(self):
        return [scrapy.Request(url=login_index_url,meta={'cookiejar': 1},headers={'Host':'passport.zujuan.com'},callback=self.post_login)]

    def post_login(self, response):
        self.logger.info(u'登录的url:%s',response.url)
        _csrf = response.xpath('.//input[@name="_csrf"]/@value').extract()[0]
        yield scrapy.FormRequest.from_response(
            response,url=login_url,meta={'cookiejar': response.meta['cookiejar']},callback=self.parse,method='POST',
            formdata={'_csrf':_csrf,'LoginForm[username]':username,'LoginForm[password]': password,'LoginForm[rememberMe]':'0'},
            headers={'Host': 'passport.zujuan.com','Origin':'http://passport.zujuan.com','X-Requested-With':'XMLHttpRequest',
                     'Referer':'http://passport.zujuan.com/login',
                     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.91 Safari/537.36',
            })

    def parse(self, response):
        rs = json.loads(response.body)
        if rs['errcode'] == 0:
            self.logger.info('登录成功，信息：%s',response.body)
        else:
            self.logger.error('登录异常,异常信息%s',response.body)
            raise RuntimeError('登录异常,异常信息')
        mongo = MongoDB()
        coll = mongo.getCollection(COLL.question)
        cursor = coll.find({'cid': subjectcode, 'status': {'$exists': False}})
        for doc in cursor:
            url = question_url % doc['question_id']
            yield scrapy.Request(
                url=url,
                meta={'cookiejar': response.meta['cookiejar']},
                headers={
                    'Host':'www.zujuan.com','Upgrade-Insecure-Requests':'1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'zh-CN,zh;q=0.8',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.91 Safari/537.36',
                },
                callback=self.parseQuestion)

    def parseQuestion(self,response):
        mock_data = re.findall(u"var\s*MockDataTestPaper\s*=\s*(\[\s*{.+?}\s*\])\s*;",response.body)[0]
        mock_data = json.loads(mock_data)
        question = mock_data[0]['questions'][0]
        if not question['answer'] and  not question['list']:
            self.logger.error(u'下载题目没有答案异常，题目Id:%s', question['question_id'])
            raise ValueError(u'下载题目没有答案')
        # if not question['explanation']:
        #     self.logger.error(u'下载题目没有解析异常，题目Id:%s',question['question_id'])
        #     raise ValueError(u'下载题目没有解析')
        item = QuestionTtem()
        if question['explanation']:
            item['status'] = 1
        else:
            item['status'] = 0
        item['question'] = question
        return item
