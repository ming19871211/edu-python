# -*- coding: utf-8 -*-

# Scrapy settings for zujuan_scrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'zujuan_scrapy'

SPIDER_MODULES = ['zujuan_scrapy.spiders']
NEWSPIDER_MODULE = 'zujuan_scrapy.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'zujuan_scrapy (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#配置并发请求量
CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#禁止使用cookies
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#设置请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept:text/html':'application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'zh-CN,zh;q=0.8',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Host':'www.zujuan.com',
    'Upgrade-Insecure-Requests':'1',
}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'zujuan_scrapy.middlewares.ZujuanScrapySpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
#    'zujuan_scrapy.middlewares.MyCustomDownloaderMiddleware': 543,
#     'zujuan_scrapy.middlewares.ProxyMiddleware': 100,
#     'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 150,
#     'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware':50,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'zujuan_scrapy.pipelines.ZujuanScrapyPipeline': 300,
#     'scrapy_redis.pipelines.RedisPipeline': 300
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

#线程池的大小
REACTOR_THREADPOOL_MAXSIZE  =  30
#禁用重试
RETRY_ENABLED = False
#logger配置 LOG_FILE  LOG_ENABLED LOG_ENCODING LOG_LEVEL  LOG_FORMAT  LOG_DATEFORMAT  LOG_STDOUT
LOG_LEVEL = 'INFO' # DEBUG、INFO、WARN、ERROR
LOG_FILE = 'zujuan_scrapy.log'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.91 Safari/537.36'


class MongoDB_CFG:
    '''MongoDB数据库配置'''
    host="127.0.0.1"
    port=27017
    db_name="zujuan"
class COLL:
    pg_url = 'zujuan_knowled_pg_url'
    question = 'zujuan_question'

rootUrl = 'http://www.zujuan.com'
knowledUrl=rootUrl+'/question?chid=%d&xd=%d&tree_type=knowledge'
curr_subject = {'chid':11,'xd':2,'subjectCode':23,'name':u'生物'}

# subjects ={
#         'chinese':{'chid':2,'name':u'语文','xds':[1,2,3],'code':6},
#         'math':{'chid':3,'name':u'数学','xds':[1,2,3],'code':0},
#         'english':{'chid':4,'name':u'英语','xds':[1,2,3],'code':7},
#         'physics':{'chid':6,'name':u'物理','xds':[2,3],'code':1},
#         'chemistry':{'chid':7,'name':u'化学','xds':[2,3],'code':2},
#         'biology':{'chid':11,'name':u'生物','xds':[2,3],'code':3},
#         'history':{'chid':8,'name':u'历史','xds':[2,3],'code':9},
#         'politics':{'chid':9,'name':u'政治思品','xds':[2,3],'code':8},
#         'geography':{'chid':10,'name':u'地理','xds':[2,3],'code':5},
# }
# scrapy-redis 配置项

# #启用redis调度储存请求队列
# SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# # 确保所有的爬虫通过redis去重
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# # 不清除redis队列、这样可以暂停/恢复 爬取）
# SCHEDULER_PERSIST = True
# # redis连接地址
# REDIS_URL = None
# REDIS_HOST = 'localhost'
# REDIS_PORT = 6379

rootImagPath = 'zj_image'
tmp_suffix = "-tmp"

