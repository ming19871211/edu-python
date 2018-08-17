#!/usr/bin/python
#-*-coding:utf-8-*-
#https://elasticsearch-py.readthedocs.io/en/master/
from elasticsearch import Elasticsearch
from elasticsearch.client import ClusterClient
import time
import re
import Utils
from config import bizs,ES_INFO,DEFAULT_PARAM,PARAM_CODE,EMAIL_INFO

logger = Utils.getLogger(__name__)
#配置参数
DAY_SECOND = 24 * 60 * 60
email = Utils.Email(EMAIL_INFO.email_host,EMAIL_INFO.email_port,EMAIL_INFO.login_user,EMAIL_INFO.login_passwd)
class ES:
    def __init__(self,hosts=ES_INFO.es_hosts,http_auth=(ES_INFO.es_user,ES_INFO.es_passwd),describe='测试环境'):
        self.hosts=hosts
        self.es=Elasticsearch(hosts=hosts,http_auth=http_auth)
        self.cluster = ClusterClient(self.es)
        self.describe=describe

    def delEsLogs(self,reserver_day=ES_INFO.RESERVER_DAY):
        '''清理es日志---reserver_day:日志保留天数（包括当天）'''
        if reserver_day < 1 :raise Exception(u'参数reserver_day值异常，不能小于1.')
        cluster_state = self.cluster.state()
        indices = cluster_state['metadata']['indices']
        zero_time = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00',time.localtime(time.time())), '%Y-%m-%d %H:%M:%S'))
        #对比时间为毫秒
        compare_time = (zero_time  - DAY_SECOND*(reserver_day-1))*1000
        log_str = u'[es主机:%s---执行时间:%s]-删除 %s 之前的日期的日志'%(str(self.hosts),time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(compare_time/1000)))
        logger.info('--------------------------start-------------------------------------')
        logger.info(log_str)
        for key,indice in indices.items():
            creation_date = int(indice['settings']['index']['creation_date'])
            if  creation_date < compare_time and self.isMatch(key):
                logger.info(u'准备删除日志名称:%s,创建时间%s ' % (key, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(creation_date / 1000))))
                self.es.indices.delete(key)
                logger.info(u'删除日志名称:%s,创建时间%s ' %(key,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(creation_date/1000))))
        logger.info('--------------------------end---------------------------------------')

    def  isMatch(self,key,es_index_pre=ES_INFO.es_index_pre):
        for partten in es_index_pre:
            if re.match(partten,key): return True

    def alertByques(self,biz, index=DEFAULT_PARAM.es_index):
        #获取参数
        lastMinute = biz.get(PARAM_CODE.LAST_TIME) if biz.has_key(PARAM_CODE.LAST_TIME) else DEFAULT_PARAM.last_time
        num_events = biz[PARAM_CODE.NUM_EVENTS] if biz.has_key(PARAM_CODE.NUM_EVENTS) else DEFAULT_PARAM.num_events
        to_addrs =  biz[PARAM_CODE.TO_ADDRS]
        ignore_realert =  biz[PARAM_CODE.IGNORE_REALERT] if biz.has_key(PARAM_CODE.IGNORE_REALERT) else DEFAULT_PARAM.ignore_realert
        name = biz[PARAM_CODE.NAME]
        last_minute =Utils.getCurrMilliSecond() - lastMinute*60*1000
        query = biz.get(PARAM_CODE.QUERY)
        body={"query":{"bool":{"must":[
            {"query_string":{"query": biz.get(PARAM_CODE.BIZ_QUERY),"analyze_wildcard":True}},
            {"range":{"@timestamp":{"gte": last_minute,"format":"epoch_millis"}}}
        ]}}}
        if query:
            body['query']['bool']['must'].insert(1,{"query_string":{"query": query,"analyze_wildcard":True}})
        rs = self.es.search(index=index,size=1000,filter_path=['hits.hits._source.container_name','hits.hits._source.log','hits.hits._source.@timestamp'],
                            sort=["@timestamp:desc"],body=body)
        if rs:
            num =  len(rs['hits']['hits'])
            if num >=num_events:
                #获取上次发警报的时间
                key = Utils.getMD5(biz)
                if not Utils.hasCache(key):
                    messages = ''
                    i =0
                    for row in rs['hits']['hits']:
                        source = row['_source']
                        container_name = source['container_name']
                        log = source['log']
                        timestamp = source['@timestamp']
                        message = '[%s---%s]:%s' %(timestamp,container_name,log)
                        messages += message
                        i += 1
                        if i >= num_events: break
                    # 发邮件
                    try:
                        email.sendmail(message=messages,to_addrs=to_addrs,topic=u'%s Elasticsearch %s 异常' % (self.describe,name))
                        logger.error(u'主机:%s，%s:已发送报警邮件，查询条件:%s，命中数量：%d', self.hosts, name, query, num)
                    except Exception:
                        logger.exception(u'主机:%s，%s:发送报警邮件失败，查询条件:%s，命中数量：%d', self.hosts, name, query, num)
                    Utils.saveCache(key,num,ignore_realert)
                else:
                    logger.info(u'主机:%s，%s-之前已发送过相同的报警，在%s分钟内不需要报警，查询条件:%s，命中数量：%d,',
                                self.hosts,name,ignore_realert,query, num)
            else:
                logger.info(u'主机:%s，%s-数量(%d)未达到发警告数量',self.hosts,name,num)
        else:
            logger.info(u'主机:%s，%s-无警告',self.hosts,name)

if __name__ == '__main__':
    es_test = ES()
    for biz in bizs:
        es_test.alertByques(biz)