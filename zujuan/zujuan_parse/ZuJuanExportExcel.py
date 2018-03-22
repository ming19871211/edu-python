#!/usr/bin/python
#-*-coding:utf-8-*-

import xlwt
from utils.SqlUtil import MongoDB
import pymongo
from cfg import COLL,subjectName_dic
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def exportQuestionTypeToExecel():
    mongon = MongoDB()
    coll = mongon.getCollection(COLL.question_type['question_channel_type'])
    question_type_dic = {}
    for doc in coll.find():
        for cid in doc['cids']:
            cid_arr = question_type_dic[cid] if question_type_dic.has_key(cid) else []
            cid_arr.append({'id':doc['id'],'name':doc['name'],'cname':subjectName_dic[cid]})
            question_type_dic[cid] = cid_arr
    book = xlwt.Workbook(encoding='utf-8', style_compression=0)
    sheet = book.add_sheet('题目类型', cell_overwrite_ok=True)
    sheet.write(0, 0, u'类型编码')
    sheet.write(0, 1, u'类型名称')
    sheet.write(0, 2, u'学科名称')
    sheet.write(0, 3, u'学科编码')
    row = 1
    for key,values in question_type_dic.items():
        for value in values:
            sheet.write(row, 0, value['id'])
            sheet.write(row, 1, value['name'])
            sheet.write(row, 2, value['cname'])
            sheet.write(row, 3, key)
            row += 1
    book.save('zujuan_question_type.xls')
def exportKnowledToExecel():
    mongon = MongoDB()
    coll = mongon.getCollection(COLL.knowled)
    book = xlwt.Workbook(encoding='utf-8', style_compression=0)
    sheet = book.add_sheet('知识点关系', cell_overwrite_ok=True)
    sheet.write(0, 0, u'学科名称')
    sheet.write(0, 1, u'学科编码')
    sheet.write(0, 2, u'一级知识点名称')
    sheet.write(0, 3, u'一级知识点编码')
    sheet.write(0, 4, u'二级知识点名称')
    sheet.write(0, 5, u'二级知识点编码')
    sheet.write(0, 6, u'三级知识点名称')
    sheet.write(0, 7, u'三级知识点编码')
    sheet.write(0, 8, u'四级知识点名称')
    sheet.write(0, 9, u'四级知识点编码')
    row = 1
    for doc in coll.find({'hasChild':False}).sort([('cid',pymongo.ASCENDING)]):
        sheet.write(row,0,subjectName_dic[doc['cid']])
        sheet.write(row,1,doc['cid'])
        writeKnowldeToSheet(doc,row,sheet,coll)
        row += 1
    book.save('zujuan_knowled.xls')

def writeKnowldeToSheet(doc,row,sheet,coll):
    level = doc['level']
    sheet.write(row,level*2,doc['title'])
    sheet.write(row,level*2+1,doc['id'])
    parentId = doc['parentId']
    if parentId:
        writeKnowldeToSheet(coll.find_one({'id':parentId}),row,sheet,coll)



if __name__ == '__main__':
    # exportQuestionTypeToExecel()
    exportKnowledToExecel()






