#!/usr/bin/env python
# -*- coding:utf-8 -*-

import scrapy
import os
import sys
import logging
import imghdr
from jyeoo_scrapy.settings import image_path, tmp_suffix
reload(sys)  
sys.setdefaultencoding('utf8')

class JyeooImageSpider(scrapy.Spider):
    name = "jyeoo_image"
    def start_requests(self):
        for parent,dir_names,file_names in os.walk(image_path):
            for file_name in file_names:
                    if file_name.endswith(tmp_suffix):   
                        file_t_name = os.path.join(parent,file_name)                     
                        with open(file_t_name,'r') as f:
                            url = f.read()
                        yield scrapy.Request(url,callback=self.parse,meta={'fileTmp':file_t_name})

    def parse(self,response): 
        print 'parseImg',response.url
        if response.status in [200]:
            fileTmp = response.meta['fileTmp']
            file = fileTmp.rstrip(tmp_suffix)
            with open(file,'wb') as f:f.writelines(response.body)
            if imghdr.what(file):
                os.remove(fileTmp)
            else:
                os.remove(file)
                logging.error(u'下载的页面返回不是图片流,url:%s' % response.url)
        else:
            logging.error(u'图片状态异常，url:%s,异常码:%d' %(response.url,response.status))
