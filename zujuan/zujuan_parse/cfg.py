#!/usr/bin/python
#-*-coding:utf-8-*-
import os
class URL:
    rootUrl = 'http://www.zujuan.com'
    knowledUrl=rootUrl+'/question?chid=%d&xd=%d&tree_type=knowledge'
    knowledJsonUrl= rootUrl + '/question/tree?id=%s&type=knowledge&_=%d'
    #输入参数 最后一级知识点Id、年级、第几页、随机时间毫秒数
    questionBatchUrl= rootUrl + '/question/list?knowledges=%s&question_channel_type=&difficult_index=&exam_type=&kid_num=&%s&sortField=time&page=%d&_=%d'
    grade ={
        1:'grade_id%5B%5D=0&grade_id%5B%5D=1&grade_id%5B%5D=2&grade_id%5B%5D=3&grade_id%5B%5D=4&grade_id%5B%5D=5&grade_id%5B%5D=6',
        2:'grade_id%5B%5D=0&grade_id%5B%5D=7&grade_id%5B%5D=8&grade_id%5B%5D=9',
        3:'grade_id%5B%5D=0&grade_id%5B%5D=10&grade_id%5B%5D=11&grade_id%5B%5D=12&grade_id%5B%5D=13',
    }
    paper_url ='http://www.zujuan.com/paper/index?chid=%d&xd=%d'
    paper_pg_url = 'http://www.zujuan.com/paper/index?chid=%d&xd=%d&page=%d&gradeid=%s&province_id=%s'

class PATH:
    rootPath='data'
    if not os.path.exists(rootPath):os.makedirs(rootPath)
subjects ={
        'chinese':{'chid':2,'name':u'语文','xds':[1,2,3],'code':6},
        'math':{'chid':3,'name':u'数学','xds':[1,2,3],'code':0},
        'english':{'chid':4,'name':u'英语','xds':[1,2,3],'code':7},
        'physics':{'chid':6,'name':u'物理','xds':[2,3],'code':1},
        'chemistry':{'chid':7,'name':u'化学','xds':[2,3],'code':2},
        'biology':{'chid':11,'name':u'生物','xds':[2,3],'code':3},
        'history':{'chid':8,'name':u'历史','xds':[2,3],'code':9},
        'politics':{'chid':9,'name':u'政治思品','xds':[2,3],'code':8},
        'geography':{'chid':10,'name':u'地理','xds':[2,3],'code':5},
        }
xds = {'primary':{'xd':1,'name':u'小学'},'middle':{'xd':2,'name':u'初中'},'high':{'xd':3,'name':u'高中'}}

subjectName_dic ={
    10:u'小学数学',20:u'初中数学',30:u'高中数学',
    16:u'小学语文',26:u'初中语文',36:u'高中语文',
    17:u'小学英语',27:u'初中英语',37:u'高中英语',
    21:u'初中物理',31:u'高中物理',
    22:u'初中化学',32:u'高中化学',
    23:u'初中生物',33:u'高中生物',
    28:u'初中政治',38:u'高中政治',
    29:u'初中历史',39:u'高中历史',
    25:u'初中地理',35:u'高中地理',
}

class COLL:
    knowled = 'zujuan_knowled_relation'
    pg_url = 'zujuan_knowled_pg_url'
    question = 'zujuan_question'
    paper = 'zujuan_paper'
    type={
        'version':'zujuan_type_version',
        'grade':'zujuan_type_grade',
        'papertype':'zujuan_type_papertype',
        'province':'zujuan_type_province'
    }
    question_type={
        'question_channel_type':'zujuan_question_channel_type',
        'difficult_index':'zujuan_question_difficult_index',
        'exam_type':'zujuan_question_exam_type',
        'grade':'zujuan_question_grade'
    }