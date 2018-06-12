#!/usr/bin/python
#-*-coding:utf-8-*-

import re
from bs4 import BeautifulSoup #lxml解析器
import json
import random
import os
import datetime
from utils import Utils
from utils.SqlUtil import PostgreSql
from ConfigParser import ConfigParser
print Utils.getMacAddress()
print Utils.getHostName()
print Utils.getIpAddr(Utils.getHostName())

config = ConfigParser()
config.read('jyeoo.cfg')
SELECTION_JYEOO = 'jyeoo'

err_ids = config.get(SELECTION_JYEOO,'err_ids').split(',')

print err_ids,type(err_ids)
