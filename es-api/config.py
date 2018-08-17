#!/usr/bin/python
#-*-coding:utf-8-*-

class EMAIL_INFO:
    email_host = 'smtp.139.com'
    email_port = 25
    login_user = 'ming19871211@139.com'
    login_passwd = 'ming1234'
class DEFAULT_PARAM:
    #将触发警报的事件数量
    num_events=2
    #查询最近时间
    last_time=2
    #忽略重复警报时间
    ignore_realert=5
    #es默认索引
    es_index='fluentd-*'
class PARAM_CODE:
    TO_ADDRS = 'to_addrs'
    CODE='code'
    NAME='name'
    BIZ_QUERY='biz_query'
    QUERY='query'
    NUM_EVENTS='num_events'
    #查询最近时间code
    LAST_TIME='last_time'
    #忽略报警时间code
    IGNORE_REALERT='ignore_realert'
class ES_INFO:
    es_hosts = ['127.0.0.1:9200']
    es_user = 'elastic'
    es_passwd = 'changeme'
    #索引前缀
    es_index_pre = ['fluentd-']
    RESERVER_DAY = 30  # 日志保留天数（包括当天,至少为1）

bizs=[
    {'code':'mbzw_gateway','name':'妙笔作文2.0网关','biz_query':'+container_name:mbzw_gateway',
     'query':'log:ERROR and log:exception ','to_addrs':['zhangweiguo@talkweb.com.cn','liaoyongjian@talkweb.com.cn']},
    {'code':'jxsls_gateway','name':'优班掌网关','biz_query':'+container_name:jxsls_gateway',
     'query':'log:ERROR and log:exception','to_addrs':['longji@talkweb.com.cn']}
]