#!/usr/bin/python
#-*-coding:utf-8-*-

import re
from bs4 import BeautifulSoup #lxml解析器
import json
import random
pt1 = '1233241dasf'
content_arr = re.findall(u'^<div\s+class=[\'"]pt1[\'"]>\s*<!--B\d+-->\s*(.*?)<span\s+class=[\'"]qseq[\'"]>[1-9]\d*．</span>(<a\s+href=.+?>)?(（.+?）)(</a>)?(.+?)<!--E\d+-->\s*</div>$',pt1)[0]

