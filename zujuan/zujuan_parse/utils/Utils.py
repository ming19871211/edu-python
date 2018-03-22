#!/usr/bin/env python
# -*- coding:utf-8 -*-

from PIL import Image
import hashlib
import os
import sys
import urlparse
reload(sys)
sys.setdefaultencoding('utf-8')

def dhash(imageFileName, hash_size = 8):
    '''得到图片的相识度MD5值'''
    # Grayscale and shrink the image in one step.
    image = Image.open(imageFileName)
    image = image.convert('L').resize((hash_size + 1, hash_size),Image.ANTIALIAS,)
    pixels = list(image.getdata())
    # Compare adjacent pixels.
    difference = []
    for row in xrange(hash_size):
        for col in xrange(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)
    # Convert the binary array to a hexadecimal string.
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2**(index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0
    return ''.join(hex_string)

def modifyMD5(fileName):
    '''修改文件的MD5值'''
    with open(fileName,'ab') as f: f.write("####&&&&")

def getFilename(url,root_path):
    '''获取url下载保存的文件全名“包含路径”'''
    url_path = urlparse.urlsplit(url)      
    return os.path.join(root_path,url_path.path[1:])

def getStrMD5(s):
    '''获取字符串的MD5码'''
    hashmd5 = hashlib.md5()
    hashmd5.update(s)
    return hashmd5.hexdigest()

def getFileMD5(fileName):
    '''获取文件的MD5码'''
    hashmd5 = hashlib.md5()
    with open(fileName,'rb') as f:hashmd5.update(f.read())
    return hashmd5.hexdigest()
def getBigFileMD5(fileName):
    '''获取大文件的MD5码'''
    hashmd5 = hashlib.md5()
    with open(fileName,'rb') as f:
        while True:
            b = f.read(8096)
            if not b : break
            hashmd5.update(b)
    return hashmd5.hexdigest()
