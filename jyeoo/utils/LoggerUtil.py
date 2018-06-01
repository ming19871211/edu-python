#!/usr/local/bin/python  
# -*-coding:utf-8-*-  
  
''''' 
Created on 2017年11月9日 
 
@author: meiqiming 
'''  
  
import logging
import logging.config
#加载日志配置文件
logging.config.fileConfig("utils/logger.conf")
def getLogger(name=None):
    return logging.getLogger(name)


