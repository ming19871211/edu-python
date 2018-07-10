#!/usr/bin/python
#-*-coding:utf-8-*-
import os
import threading
import pickle
from utils import LoggerUtil
from config import PATH
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
logger = LoggerUtil.getLogger(__name__)

from jyeoo_parse_pic import ExtractPicture,ParseImage

class JyeooHandle:
    def __init__(self):
        # 获取处理标记
        self.__h_file_name = '%s-handleInfo.pkl' % (PATH)
        try:
            info = pickle.load(open(self.__h_file_name, "rb"))
        except Exception:
            info = {'step': 1}
        self.handleInfo = info

    def __saveHandleInfo(self):
        self.handleInfo['step'] += 1
        pickle.dump(self.handleInfo, open(self.__h_file_name, "wb"))

    def __execExtractPicture(self):
        '''提取图片'''
        extractPic = ExtractPicture()
        if not extractPic.execExtract():
            logger.error(u'提取图片，未完成！')
            raise Exception(u'提取图片，未完成！')
        logger.info(u'提取图片流程完成！')
        self.__saveHandleInfo()

    def __execScrapyImage(self):
        '''启动爬虫进行爬取'''
        for i in range(0, 3):
            print u'开启主jyeoo_image爬虫第%d次' % (i + 1)
            os.system('scrapy crawl jyeoo_image')
            for t in threading.enumerate():
                if t is threading.currentThread():
                    continue
                t.join()
        # 获取未下载的图片数量
        tmp_count = 0
        for parent, dir_names, file_names in os.walk(PATH.picture_path):
            for file_name in file_names:
                if file_name.endswith(PATH.tmp_suffix): tmp_count += 1
        if tmp_count > 0:
            logger.error(u'爬取图片流程，未完成，临时图片数量还剩:%d', tmp_count)
            raise Exception(u'爬取图片流程，未完成，临时图片数量还剩:%d', tmp_count)
        logger.info(u'爬取图片流程完成！')
        self.__saveHandleInfo()

    def __execParseImage(self):
        parseImage = ParseImage()
        if not parseImage.execParseImage():
            logger.error(u'处理图片，未完成！')
            raise Exception(u'处理图片，未完成！')
        logger.info(u'处理图片流程完成！')
        self.__saveHandleInfo()

    def execProcess(self):
        if self.handleInfo['step'] == 1:
            self.__execExtractPicture()
        if self.handleInfo['step'] == 2:
            self.__execScrapyImage()
        if self.handleInfo['step'] == 3:
            self.__execParseImage()


if __name__ == '__main__':
    jyeooHandle = JyeooHandle()
    jyeooHandle.execProcess()

