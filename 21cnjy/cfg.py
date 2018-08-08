#!/usr/bin/python
#-*-coding:utf-8-*-
from ConfigParser import ConfigParser
config = ConfigParser()
config.read('21cnjy.cfg')
SELECTION_21CN='21cnjy'
def getCFG(params_name,default=None):
    return config.get(SELECTION_21CN,params_name) if config.has_option(SELECTION_21CN,params_name) else default

class URL:
    ROOT_URL = getCFG('root_url','https://zujuan.21cnjy.com')
class COLL:
    SELECTION = 'jyeoo_selection_relation'
