#!/usr/bin/python
#-*-coding:utf-8-*-

# !/usr/bin/env python
# *-* coding:utf-8 -*-

import os
import re
import urlparse
import json
from utils import LoggerUtil,Utils
from utils.SqlUtil import PostgreSql
from config import PATH, SQL,image_url
import shutil
import sys
reload(sys)
sys.setdefaultencoding('utf8')
logger = LoggerUtil.getLogger(__name__)
tmp_suffix = PATH.tmp_suffix

class JyeooUtil:
    @staticmethod
    def getJyeooImg(str):
        return re.findall(u'[\"|\'](https?://img.jyeoo.net/.*?)[\\\]?[\"|\']', str)

class ExtractPicture:
    def __init__(self):
        pass
    def __getFilename(self,url, root_path=PATH.picture_path):
        url_path = urlparse.urlsplit(url)
        return os.path.join(root_path, url_path.path[1:])
    def __generateTmpImage(self,urls,pg,select_convert_sql=SQL.select_convert_sql):
        '''生成临时的图片文件'''
        for url in urls:
            if pg.getOne(select_convert_sql,(url,)):continue
            url_file = self.__getFilename(url)
            tmp_file = url_file + tmp_suffix
            dirname = os.path.dirname(url_file)
            if (not os.path.exists(url_file)) and (not os.path.exists(tmp_file)):
                if not os.path.exists(dirname): os.makedirs(dirname)
                with open(tmp_file, 'w+') as f:
                    f.write(url)
    def execExtract(self,select_main_sql=SQL.select_main_sql, insert_image_sql=SQL.insert_image_sql,
                    update_main_sql=SQL.update_main_sql,select_convert_sql=SQL.select_convert_sql):
        '''执行提取图'''
        postgreSql = PostgreSql()
        count = 0
        rs = True
        try:
            flag = True  # 代表数据库里面还有需要处理的数据
            while flag:
                try:
                    flag = False
                    insert_image_params = []
                    update_main_params = []
                    for rows in postgreSql.getAll(select_main_sql):
                        flag = True
                        seq = rows[0]
                        qid = rows[1]
                        try:
                            urls = []
                            for col in rows[2:]:
                                for j_url in JyeooUtil.getJyeooImg(col):
                                    if j_url not in urls:
                                        urls.append(j_url)
                            # 生成临时的图片文件
                            self.__generateTmpImage(urls,postgreSql,select_convert_sql)
                            # 插入数据到img表
                            insert_image_params.append((seq,qid,json.dumps(urls), 0 if urls else 2))
                            # 更新jyeoo主表的数据状态
                            update_main_params.append((1 if urls else 2, qid))
                        except Exception as ex:
                            rs = False
                            logger.exception(u"提取图片-----处理qi=%s，创建题目的图片发生异常,异常信息：%s" % (qid, ex.message))
                    return rs
                    if insert_image_params: postgreSql.batchExecute(insert_image_sql, insert_image_params)
                    if update_main_params: postgreSql.batchExecute(update_main_sql, update_main_params)
                    postgreSql.commit()
                    count += len(insert_image_params)
                    logger.info(u'提取图片-----已成功处理题目数量:%d' % count)
                except Exception as e:
                    postgreSql.rollback()
                    rs = False
                    logger.exception(u"提取图片-----批量处理-异常信息:%s" % (e.message))
        finally:
            postgreSql.close()
        return rs

#####处理图片#######
class ParseImage:
    def isNotTmpFile(self,fileName, tmp_suffix=PATH.tmp_suffix):
        '''不是临时文件'''
        return not fileName.endswith(tmp_suffix)
    def execParseImage(self,select_image_sql=SQL.select_image_sql, select_convert_sql=SQL.select_convert_sql,
                       update_main_url_sql=SQL.update_main_url_sql, update_image_sql=SQL.update_image_sql,
                       insert_convert_sql=SQL.insert_convert_sql,
                       picture_path=PATH.picture_path, pic_new_path=PATH.pic_new_path,
                       pic_relative_path = PATH.pic_relative_path,image_url = image_url):
        pic_new_real_path =  os.path.join(pic_new_path,pic_relative_path)
        image_real_url = urlparse.urljoin(image_url,pic_relative_path)
        logger.info(u'进入处理图片流程，原始图片路径：%s，处理后图片存放路径：%s，图片url前缀地址：%s'
                    ,picture_path,pic_new_real_path, image_real_url)
        if not os.path.exists(pic_new_real_path): os.makedirs(pic_new_real_path)
        postgreSql = PostgreSql()
        count = 0
        total = 0
        rs = True
        try:
            flag = True  # 代表数据库里面还有需要处理的数据
            id = 0
            while flag:
                try:
                    flag = False
                    update_main_params = []
                    update_image_params = []
                    insert_convert_params = []
                    for rows in postgreSql.getAll(select_image_sql % id):
                        flag = True
                        total += 1
                        id = rows[0] if rows[0] > id else id
                        qid = rows[1]
                        urls = rows[2]
                        try:
                            isDownloadFinish = True
                            urlMap = {}
                            for url in json.loads(urls):
                                url_path = urlparse.urlsplit(url)
                                fileName = os.path.join(picture_path, url_path.path[1:])
                                if os.path.exists(fileName):
                                    (temp, extension) = os.path.splitext(fileName)
                                    # 新文件名称
                                    file_new_name = "%s%s" % (Utils.getStrMD5(url + "-mqm"), extension)
                                    # 新文件名称 - 全名
                                    file_new_name_all = os.path.join(pic_new_path, file_new_name)
                                    # 新的url
                                    url_new = image_real_url + file_new_name
                                    urlMap[url] = url_new
                                    if os.path.exists(file_new_name_all):
                                        if not postgreSql.getOne(select_convert_sql, (url,)):
                                            insert_convert_params.append(url,url_new)
                                    else:
                                        shutil.copy2(fileName, file_new_name_all)
                                        Utils.modifyMD5(file_new_name_all)
                                        insert_convert_params.append((url, url_new))
                                else:
                                    #查询
                                    rs =  postgreSql.getOne(select_convert_sql, (url,))
                                    if rs:
                                        urlMap[url] = rs[0]
                                    else:
                                        isDownloadFinish = False
                            # 下载完成就更新t_jyeoo_img_url
                            if isDownloadFinish:
                                update_image_params.append((1, qid))
                                # 设置替换的图片url、更新原始数据表的状态为3（有图片、图片下载完成）
                                update_main_params.append((json.dumps(urlMap), 3, qid))
                        except Exception as ex:
                            rs = False
                            logger.exception(u"处理图片流程，qi=%s，校验题目的所有图片下载是否完成发生异常,异常信息：%s" % (qid, ex.message))
                    return rs
                    if update_main_params: postgreSql.batchExecute(update_main_url_sql, update_main_params)
                    if update_image_params: postgreSql.batchExecute(update_image_sql, update_image_params)
                    if insert_convert_params: postgreSql.batchExecute(insert_convert_sql, insert_convert_params)
                    postgreSql.commit()
                    count += len(update_image_params)
                    logger.info(u'处理图片流程，已成功处理题目数量:%d，校验题目数量总数:%d' % (count, total))
                except Exception as e:
                    rs = False
                    postgreSql.rollback()
                    logger.exception(u"处理图片流程，批量处理-异常信息:%s" % (e.message))
        finally:
            postgreSql.close()
        return rs



