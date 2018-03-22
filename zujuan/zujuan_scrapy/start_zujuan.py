#!/usr/bin/python
#-*-coding:utf-8-*-

import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

if __name__ == '__main__':
    os.system('scrapy crawl zujuan_knowled_question')