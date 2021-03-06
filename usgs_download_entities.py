#
# -*-coding:utf-8 -*-
#
# @Author: zhaojianghua
# @Date  : 2018-03-09 20:25
#


import os, sys
import re
import usgsutils
import shutil
import requests
from urllib.parse import urlencode
from urllib.request import urlopen, install_opener, build_opener, HTTPCookieProcessor, Request
from datetime import datetime

MSG_OK = "Success"  # OK
MSG_EORDER = "Order"
MSG_SKIP = "Skip"  # SKIP
MSG_EDATA = "Error"  # File error

user_agent = {'User-agent': "Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36" }

def successError(msg):
    sys.stderr.write("Success: " + msg + "\n");


def sysInfo(msg):
    sys.stderr.write("Info: " + msg + "\n");


def parse_Usgs_DownloadURL(dataid, html, product=None):
    try:
        # downloadOptions = re.findall('<input type="button" title="(.*?)" (disabled="disabled" class="disabled")? onClick="window.location=\'(.*?)\'" .+' , html)
        downloadOptions = re.findall(
            '<div class="row clearfix">[\w\W]+?<input[\w\W]+?title="([\w\W]+?)"[\w\W]+?window.location=\'([\w\W]*?)\'[\w\W]+?<div class="name">([\w\W]+?)</div>',
            html)
        dl_url = None

        # print >> sys.stderr, "\n", "downloadOptions:", downloadOptions, "\n"

        for do in downloadOptions:
            sname = do[0].lower()
            skey = "Processing".lower()

            if sname.find(skey) >= 0:
                return "Processing"

        dl_url = downloadOptions[-1][1]
        return dl_url

    except Exception as e:
        print(e)  # >> sys.stderr, e

    return None


def entity_download_request(dataId, outfile, product=None):
    # login
    cookies = HTTPCookieProcessor()
    opener = build_opener(cookies)
    install_opener(opener)

    data = urlopen("https://ers.cr.usgs.gov").read().decode('utf-8')
    m = re.search(r'<input .*?name="csrf_token".*?value="(.*?)"', data)
    if m:
        token = m.group(1)
    else:
        print("Error : CSRF_Token not found")

    params = urlencode(dict(username='wangxz79@163.com', password='wangxz79', csrf_token=token))
    # params = "password=wangxz79&csrf_token=rYZ0%2Fw%3D%3D&username=wangxz79%40163.com"
    params = params.encode('ascii')
    request = Request("https://ers.cr.usgs.gov/login", params, headers={})
    f = urlopen(request)

    data = f.read().decode('utf-8')

    f.close()
    if data.find('You must sign in as a registered user to download data or place orders for USGS EROS products') > 0:
        print("Authentification failed")
    print("login success")

    # dataid to url
    dataset_name = usgsutils.parse_Usgs_DatasetName(dataId)
    dataset_id = str(usgsutils.parse_Usgs_DatasetId(dataId))
    dataurl = "https://earthexplorer.usgs.gov/download/options/" + dataset_id + "/" + dataId

    print("简析下载选项")
    r = requests.get(dataurl)
    dl_url = parse_Usgs_DownloadURL(dataId, r.text, product)

    # resp = myhttplib.urlopen("https://earthexplorer.usgs.gov/download/options/" + dataset_id + "/" + dataId,
    #                          headers=myhttplib.ajax_header)
    # if myhttplib.response_read(resp, s.write) is None:
    #     sysError("打开USGS下载选项页面失败，请稍候重试！");
    #     return None, -2, "打开USGS下载选项页面失败，请稍候重试！"
    #
    # options_html = s.getvalue()
    # sysInfo(options_html)
    #
    # sysInfo("简析下载选项")
    # dl_url = parse_Usgs_DownloadURL(dataId, options_html, product)


    if dl_url is None:
        print("没有产品实体信息！")
        return None, -1, "没有产品实体信息！"

    print(dl_url)
    # url = "https://earthexplorer.usgs.gov/download/12864/LC81561192017038LGN00/STANDARD/EE"
    url = dl_url
    req = urlopen(url)
    # req1 = urllib.urlopen(url)

    uri = req.url
    print(uri)

    # t1 = datetime.now()
    # print(t1)
    # with requests.get(uri, stream=True) as res:
    #     if res.status_code != 200:
    #         print("下载数据失败，请稍候重试！")
    #         return None, -2, "下载数据失败，请稍候重试！"
    #     with  open(outfile, 'wb') as f:
    #         try:
    #             for n, chunk in enumerate(res.iter_content(chunk_size=512), start=1):
    #                 f.write(chunk)
    #                 print("downloading ", str(n))
    #                 return "Success", 2, "下载完成！"
    #         except Exception as e:
    #             print(e)
    #             return MSG_EDATA, -2, "下载数据失败！"
    #         finally:
    #             f.close()
    #
    # t2 = datetime.now()
    # print(t2)
    # delta = t2 - t1
    # print(delta.total_seconds())

from urllib.parse import urlencode
def get_login_params(login_file):
    f = open(login_file,'r')
    data = f.read()
    m = re.search(r'<input .*?name="csrf_token".*?value="(.*?)"', data)
    if m:
        token = m.group(1)
    else:
        print("Error : CSRF_Token not found")
    params = urlencode(dict(username='wangxz79@163.com', password='wangxz79', csrf_token=token))
    return params

def entity_download(dataId, outfile, product=None):
    # dataid to url
    dataset_id = str(usgsutils.parse_Usgs_DatasetId(dataId))
    dataurl = "https://earthexplorer.usgs.gov/download/options/" + dataset_id + "/" + dataId

    print("简析下载选项")
    r = requests.get(dataurl)
    dl_url = parse_Usgs_DownloadURL(dataId, r.text, product)

    if dl_url is None:
        print("没有产品实体信息！")
        return None, -1, "没有产品实体信息！"

    print(dl_url)
    cookie_file = '/tmp/cookies.txt'
    login_file = "/tmp/login.rsp"
    try:
        wget1 = "wget --keep-session-cookies --save-cookies %s --user-agent=%s -O %s https://ers.cr.usgs.gov/"%(cookie_file, user_agent, login_file)
        print(wget1)
        os.system(wget1)
        # grep authenticity_token login.rsp

        params = get_login_params(login_file)

        wget2 = '''wget --load-cookies %s --keep-session-cookies --save-cookies %s --user-agent=%s --post-data="%s" https://ers.cr.usgs.gov/login''' % (cookie_file, cookie_file,user_agent, params)
        print(wget2)
        os.system(wget2)
        wget3 = 'wget -c -4 --load-cookies %s --user-agent=%s -O %s %s '%(cookie_file,user_agent, outfile, dl_url)
        print(wget3)
        os.system(wget3)
    except Exception as e:
        print(e)
        return MSG_EDATA, -2, "下载数据失败！"
    #  https://earthexplorer.usgs.gov/download/12864/LC81160322018017LGN00/STANDARD/EE


    return "Success", 2, "下载完成！"

if __name__ == '__main__':
    # url = "https://earthexplorer.usgs.gov/download/12864/LC81561192017038LGN00/STANDARD/EE"
    entity_download('LT51300422011320BKT00', '/dev/shm/test.tar.gz', product=None)


    # wget1 =  "wget --keep-session-cookies --save-cookies cookies.txt -O login.rsp https://ers.cr.usgs.gov/"
    # # grep authenticity_token login.rsp
    # params = get_login_params("./login.rsp")
    # # with open("login.rsp", 'rb') as f:
    # #     data = f.read()
    # #     m = re.search(r'<input .*?name="csrf_token".*?value="(.*?)"', data)
    # #     if m:
    # #         token = m.group(1)
    # #     else:
    # #         print("Error : CSRF_Token not found")
    # # params = urlencode(dict(username='wangxz79@163.com', password='wangxz79', csrf_token=token))
    # wget2 = "wget --load-cookies cookies.txt --keep-session-cookies --save-cookies cookies.txt --post-data=%s https://ers.cr.usgs.gov/login"%params
    # wget3 = 'wget --load-cookies cookies.txt -O test.tar.gz https://earthexplorer.usgs.gov/download/12864/LC81561192017038LGN00/STANDARD/EE' --inet4-only

    # wget --keep-session-cookies --save-cookies cookies.txt --user-agent={'User-agent': "Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36" } -O login.rsp https://ers.cr.usgs.gov/
    # wget --load-cookies cookies.txt --keep-session-cookies --save-cookies cookies.txt --user-agent={'User-agent': "Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36" } --post-data="password=wangxz79&csrf_token=xqvcqQ%3D%3D&username=wangxz79%40163.com" https://ers.cr.usgs.gov/login
    # wget -c -4 --load-cookies cookies.txt --user-agent={'User-agent': "Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36" } -O test.tar.gz https://earthexplorer.usgs.gov/download/12864/LC81561192017038LGN00/STANDARD/EE