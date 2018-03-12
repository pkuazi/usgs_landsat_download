#
# -*-coding:utf-8 -*-
#
# @Author: zhaojianghua
# @Date  : 2018-03-09 20:25
#


import os
import re
import usgsutils
import requests
from urllib.parse import urlencode
from urllib.request import urlopen, install_opener, build_opener, HTTPCookieProcessor, Request

MSG_OK = "Success"  # OK
MSG_EORDER = "Order"
MSG_SKIP = "Skip"  # SKIP
MSG_EDATA = "Error"  # File error

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
        print(e)# >> sys.stderr, e

    return None

def entity_download(dataId, outfile,product=None):
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
    response = requests.get(uri, stream=True, timeout=90)
    print(response.status_code)
    if response.status_code == 200:
        try:
            with open(outfile, 'wb') as f:
                count = 0
                for chunk in response.iter_content(chunk_size=1024*1024*2): # 1024*1024=1MB
                    print(count)
                    f.write(chunk)
                    count = count + 1
        except:
            return MSG_EDATA, -2, "下载数据失败！"
    return "Success", 2, "下载完成！"


