#!/usr/bin/python
#-*-coding:utf-8-*-
from ZJ21cnjy import ZJ21cnjy

if __name__ == '__main__':
    zj21cnjy = ZJ21cnjy()
    #下载题目
    zj21cnjy.downloadQuestions(ques_type=1)
    #分析提取图片的url，生成临时图片文件
    # zj21cnjy.extractQuesImage()
    #爬取图片

    #验证图片是否下载完成，下载完成进行标记