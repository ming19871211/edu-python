#!/usr/bin/python
#-*-coding:utf-8-*-

import re
from bs4 import BeautifulSoup #lxml解析器
import json
html = None
with open('text.txt', 'r') as f: html = f.read()
box_soup = BeautifulSoup(html, 'lxml')
print box_soup.find('input', attrs={'checked': 'checked'}, class_="radio s")
labe_soup = box_soup.find('input', attrs={ 'checked': 'checked'}, class_="radio s").find_parent()
answer = re.findall(u'^([A-Z])．.+$', labe_soup.get_text())[0]
# 解析知识点
point_soup = box_soup.find('em', text=u'【考点】')
points = []
for a_soup in point_soup.find_next_siblings('a'):
    know_name = a_soup.get_text()
    know_id = re.findall(u"openPointCard\(\s*'[a-zA-Z\d]+?'\s*,\s*'([a-zA-Z\d]+?)'\s*\);\s*return\s*false;\s*",a_soup['onclick'])[0]
    points.append({'code': know_id, 'name': know_name})

points = json.dumps(points, ensure_ascii=False)
analysis_soup = box_soup.find('em', text=u'【分析】').parent
print analysis_soup
analysis = re.findall(u'<div\s+class="pt[\d]"\s*>\s*<!--B[\d]-->\s*(.+?)<!--E[\d]-->\s*</div>', unicode(analysis_soup))[0].replace(u'<em>【分析】</em>', '')
#
print answer, analysis, points

