#!/usr/bin/python
#-*-coding:utf-8-*-

import requests
import random
import HTMLParser
from bs4 import BeautifulSoup #lxml解析器
import sys
reload(sys)
sys.setdefaultencoding('utf8')

html_parser = HTMLParser.HTMLParser()


CATEGORY_URL = 'http://www.jyeoo.com/chinese/ques/partialcategory'

class JyeooSelection:
    def __init__(self):
        self.session = requests.Session()
    def mainSelection(self,c_url,category_url=CATEGORY_URL):
        response = self.session.get(c_url)
        root_soup = BeautifulSoup(html_parser.unescape(response.content), "lxml")
        ul_soup = root_soup.find('ul',id='JYE_BOOK_TREE_HOLDER')
        for ek_li_soup in ul_soup.find_all('li',attrs={'ek':True}):
            print ek_li_soup['ek'],ek_li_soup['nm']
            for bk_li_soup in ek_li_soup.find_all('li',attrs={'bk':True}):
                bk_id = bk_li_soup['bk']
                bk_name = bk_li_soup['nm']
                print  bk_id,bk_name
                data = {'a':bk_id,'q':'','f':0,'cb':'_setQ','r':random.random()}
                resp = self.session.post(category_url,data=data)
                pk_ul_soup = BeautifulSoup(html_parser.unescape(resp.content), "lxml").find('ul',id='JYE_POINT_TREE_HOLDER')
                self.pareSelection(pk_ul_soup)

    def pareSelection(self,ul_soup):
        for li in  ul_soup('li',attrs={'pk':True}):
            pk_id = li['pk']
            pk_name = li['nm']
            print pk_id,pk_name
            #self.pareSelection()


if __name__ == '__main__':
    selection = JyeooSelection()
    c_url = 'http://www.jyeoo.com/chinese/ques/search?f=0'
    selection.mainSelection(c_url)
