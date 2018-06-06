#!/usr/bin/python
#-*-coding:utf-8-*-

import re
from bs4 import BeautifulSoup #lxml解析器
import json


a = u'''<div class="box-wrapper" style="left: 183px; top: 50%; z-index: 1031; visibility: visible; opacity: 1; position: fixed; margin-top: -272px;"><div class="box-inner" style="width: 1000px;"><div class="title-bar"><h2>试题详情</h2><input class="smbtn hclose" title="关闭" type="button"></div><div class="body-content" style="height: 444px;">
<div class="fright" style="margin:5px;">
    <div class="pt9-error">
        <i class="icon i-error"></i>
        <a href="javascript:void(0)" onclick="_openComment(this)" style="margin-right:5px;" ondbclick="fixbox()">纠错</a>
        <div class="error-box" style="display:none;">
            <a href="javascript:void(0)" class="btn-close" onclick="_closeComment(this)">×</a>
            <span class="angle"><i></i></span>
            <div>
                <span>解析质量：</span>
                <label title="思路清晰，解答条理"><input value="10" name="rbScore" checked="checked" type="radio">好</label>
                <label title="思路较清晰，解答较条理"><input value="8" name="rbScore" type="radio">中</label>
                <label title="分析简单，解答模糊或有错误"><input value="4" name="rbScore" type="radio">差</label>
            </div>
            <div>
                <textarea id="tbComment"></textarea>
            </div>
            <div class="tright">
                <button class="btn btn-blue btn-lg" onclick="submitComment(false,'math','6a52d104-a15a-415f-95a0-197630cc1253','3')">确定</button>
            </div>
        </div>
    </div>
    <a href="javascript:void(0)" onclick="openConfirm('【下载确认】','math','6a52d104-a15a-415f-95a0-197630cc1253','1')"><i class="icon i-download"></i>下载</a>
</div>
<fieldset id="55c5a098-4437-473e-8d20-6ea4f00180ec" class="quesborder" s="math" data-cate="1"><div class="pt1"><!--B1--><span class="qseq"></span>
（2017秋•嘉祥县期末）下列说法中正确的有（　　）<br>A．3.14不是分数<br>B．-2是整数<br>C．数轴上与原点的距离是2个单位的点表示的数是2<br>D．两个有理数的和一定大于任何一个加数<!--E1--></div><div class="pt2"><!--B2--><table style="width:100%" class="ques quesborder"><tbody><tr><td style="width:23%" class="selectoption"><label class=" s"><input name="QA_55c5a098-4437-473e-8d20-6ea4f00180ec" id="QA_55c5a098-4437-473e-8d20-6ea4f00180ec_0" value="0" class="radio s" checked="checked" disabled="disabled" type="radio">A．1个</label></td><td style="width:23%" class="selectoption"><label class=""><input name="QA_55c5a098-4437-473e-8d20-6ea4f00180ec" id="QA_55c5a098-4437-473e-8d20-6ea4f00180ec_1" value="1" class="radio" disabled="disabled" type="radio">B．2个</label></td><td style="width:23%" class="selectoption"><label class=""><input name="QA_55c5a098-4437-473e-8d20-6ea4f00180ec" id="QA_55c5a098-4437-473e-8d20-6ea4f00180ec_2" value="2" class="radio" disabled="disabled" type="radio">C．3个</label></td><td style="width:23%" class="selectoption"><label class=""><input name="QA_55c5a098-4437-473e-8d20-6ea4f00180ec" id="QA_55c5a098-4437-473e-8d20-6ea4f00180ec_3" value="3" class="radio" disabled="disabled" type="radio">D．4个</label></td></tr></tbody></table><!--E2--></div><div class="ptline"></div><div class="pt3"><!--B3--><em>【考点】</em><a href="http://www.jyeoo.com/math/ques/detail/55c5a098-4437-473e-8d20-6ea4f00180ec" onclick="openPointCard('math','19');return false;">有理数的加法</a>；<a href="http://www.jyeoo.com/math/ques/detail/55c5a098-4437-473e-8d20-6ea4f00180ec" onclick="openPointCard('math','13');return false;">数轴</a>．<div id="ja011" style="display:inline-block;"><div class="point-video"><a href="http://a.jyeoo.com/go?id=41aaa2c6e25541e2821a7d099dae7906&amp;u=348F48E5A3787153964D91C0B8F8932408E92DBCDAE18970D70F0CBD3B651E78E63C0179A2C2D05677E3B8E6C8013D81B5E95CAF0210B8CD69DA25CA6AE4BEE453269A9B119A97AC13A534A0FA3A582B" target="_blank"><em class="btn-ui video"></em>有理数的加法</a></div></div><!--E3--></div><div class="pt4"><!--B4--><em>【专题】</em>常规题型；实数．<!--E4--></div><div class="pt5"><!--B5--><em>【分析】</em>各项利用有理数的加法法则，有理数的定义判断即可．<!--E5--></div><div class="pt6"><!--B6--><em>【解答】</em>解：A．3.14是有限小数，是分数，此说法错误；<br>B．-2是负整数，此说法正确；<br>C．数轴上与原点的距离是2个单位的点表示的数是2和-2，此说法错误；<br>D．两个有理数的和不一定大于任何一个加数，此说法错误；<br>故选：A．<!--E6--></div><div class="pt7"><!--B7--><em>【点评】</em>此题考查了有理数的加法，以及有理数，熟练掌握运算法则是解本题的关键．<!--E7--></div><div class="pt9"><span class="qcp">声明：本试题解析著作权属菁优网所有，未经书面同意，不得复制发布。</span><!--B9--><span>答题：<input class="vip210" disabled="" type="button">三界无我老师　2018/5/6</span><!--E9--></div></fieldset>



</div><div class="footer-bar" style="display: block;"><span class="h1 fright"><a href="http://www.jyeoo.com/math/ques/detail/6a52d104-a15a-415f-95a0-197630cc1253" target="_blank" type="button" class="fright btn btn-blue btn-lg">转入页面式查看</a></span><span class="h0"></span></div></div></div>，
'''
b = u'bas'
c = u'下列说法中正确的有（　　）<br/>A．3.14不是分数<br/>B．-2是整数<br/>C．数轴上与原点的距离是2个单位的点表示的数是2<br/>D．两个有理数的和一定大于任何一个加数'
d = u'下列说法中正确的有（　　）<br/>A．3.14不是分数<br/>B．-2是整数<br>C．数轴上与原点的距离是2个单位的点表示的数是2<br/>D．两个有理数的和一定大于任何一个加数'
d = d.replace('<br/>','<br>')
print a.find(b),a.find(c),a.find(d)