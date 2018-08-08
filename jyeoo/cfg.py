#!/usr/bin/python
#-*-coding:utf-8-*-
class URL:
    ROOT_URL = 'http://www.jyeoo.com'
    CATEGORY_URL = 'http://www.jyeoo.com/%s/ques/partialcategory'
    C_URL = 'http://www.jyeoo.com/%s/ques/search?f=0'
    # pd - 排序，时间倒序-1，顺序-0； pi - 分页；   r - 随机数； q - 章节ID；   f - 章节-0，知识-1。
    QUES_PG_URL = 'http://www.jyeoo.com/%s/ques/partialques?f=0&q=%s&lbs=&pd=%s&pi=%s&r=%s'
    S_MAIN_URL = 'http://www.jyeoo.com/%s/ques/search?f=0'

class COLL:
    SELECTION = 'jyeoo_selection_relation'
