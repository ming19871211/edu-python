#!/usr/bin/python
#-*-coding:utf-8-*-

class PATH:
    #图片存放路径
    picture_path = 'pic-20180710/'
    #加工后的图片存放根路径
    pic_new_path = 'pic-20180710-new/'
    #加工后的图片相对路径
    pic_relative_path ='1/2018/07'
    #临时文件后缀
    tmp_suffix = "-tmp"
image_url = 'http://image.yuncelian.com/'
class SQL:
    #查询主表
    select_main_sql = "SELECT seq,qid,answer,analyses,content,options from  t_ques_jyeoo_20180601 where status = 0  LIMIT 1000"
    #主表状态更新
    update_main_sql = "update t_ques_jyeoo_20180601 set status = %s where qid = %s "
    # 更新主表的url_relation字段
    update_main_url_sql = "UPDATE t_ques_jyeoo_20180601 set url_relation  = %s, status = %s where qid = %s "

    # 查询image表
    select_image_sql = "SELECT id,qid,urls,status from t_jyeoo_img_url where status = 0 and id > %d order by id LIMIT 1000"
    # 更新image表
    update_image_sql = "UPDATE t_jyeoo_img_url set status = %s where qid = %s "
    #插入image表
    insert_image_sql= "insert into t_jyeoo_img_url (id,qid,urls,status) values(%s,%s,%s,%s)"

    #查询图片转换表
    select_convert_sql = "select new_jyeoo_url from t_jyeoo_image_convert where old_jyeoo_url = %s"
    #插入图片转换表
    insert_convert_sql = 'INSERT INTO t_jyeoo_image_convert(old_jyeoo_url,new_jyeoo_url) values(%s,%s)'


