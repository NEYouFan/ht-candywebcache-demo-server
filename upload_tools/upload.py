# -*- coding:utf-8 -*-

import requests
import sys
import json
import os
import hashlib
import base64
from Crypto.Cipher import DES

SERVER_IS_LATEST = 0              # 服务端已经是最新的
SERVER_NEED_UPLOAD = 1            # 服务端有这个资源,但是版本较旧,可以更新
SERVER_NOT_THIS_RES = 2           # 服务端没有这个资源
SERVER_OTHER_ERROR = 3            # 服务端有错误,不执行上传


# 用于设置相关信息的config项
config_items = {
    "resID": "login",
    "resVersion": "20160704",
    "appID": "kaola",
    "domain": "www.baidu.com,www.163.com",
    "zipPath": "/Users/hzhehui/workspace/web-cache/NEYouFan/ht-candywebcache-demo-server/test_packages/login_20160704.zip"
}
#################### 配置项


base_version_info = {
    "appVersion": "1.0.0",
    "appID": config_items["appID"],
    "resID": config_items["resID"],
    "resVersion": config_items["resVersion"],
    "domain": config_items["domain"],
    "zipPath": config_items["zipPath"],
    "fileServerPath": ".",
    "root_url": "http://localhost:8000/packages/"
}

post_data = {
    "appID": config_items["appID"],
    "resID": config_items["resID"]
}


def get_zippath():
    """
    执行脚本参数处理
    :return:
    """
    if len(sys.argv) == 2:
        base_version_info["zipPath"] = sys.argv[1]
        return True
    else:
        print("Usage:\t\tpython upload.py zip_file_path")
        return False


def upload_package_file(old_file):
    """
    执行上传
    :param old_file:
    :return:
    """
    url_path = "http://localhost:8080/api/upload_version"
    version_item = {}
    if create_version_info(version_item, old_file):
        post_json = []
        # post_data = json.dumps(post_json.append(version_item))
        post_json.append(version_item)

        ret = do_post(url_path, post_json)
        print(ret)
    else:
        print("upload_package_file: create_version_info Failed.")

    return

def create_md5(diff_file_name):
    """
        加密处理的
        :param diff_file_name:
        :return:
        """
    
    md5_value = hashlib.md5(diff_file_name.encode()).hexdigest()
    des_obj = DES.new("12344321")
    output_value = base64.b64encode(des_obj.encrypt(md5_value))
    
    
    return str(output_value, encoding="utf-8")


def create_version_info(version_item, old_file):
    """
    生成其他信息
    :return:
    """
    try:
        # 文件拷贝
        copy_cmd = "cp " + base_version_info["zipPath"] + " " + base_version_info["fileServerPath"] + "/packages/"
        if os.system(copy_cmd) != 0:
            return False

        # 生成相关信息
        tmp, package_name = os.path.split(base_version_info["zipPath"])
        diff_name = package_name.split("_")[0]

        if old_file != "":
            # 生成diff文件的格式: ./bsdiff packages/login_20160703.zip packages/login_20160803.zip packages/login.diff
            p, file_name = os.path.split(old_file)
            cmd = "./bsdiff " + "packages/" + file_name + " packages/" + package_name + " packages/" + diff_name + ".diff"
            os.system(cmd)
            diff_file_name = diff_name + ".diff"
            #version_item["diffMd5"] = hashlib.md5(diff_file_name.encode()).hexdigest()
            version_item["diffMd5"] = create_md5(diff_file_name)
            version_item["diffUrl"] = base_version_info["root_url"] + diff_name + ".diff"
        else:
            version_item["diffMd5"] = ""                # 首包,然后diff为空
            version_item["diffUrl"] = ""

        version_item["appVersion"] = base_version_info["appVersion"]          # 该值待定
        version_item["appID"] = base_version_info["appID"]
        version_item["domain"] = base_version_info["domain"]
        version_item["resID"] = base_version_info["resID"]
        version_item["resVersion"] = base_version_info["resVersion"]

        version_item["fullUrl"] = base_version_info["root_url"] + package_name
        version_item["fullMd5"] = create_md5(version_item["fullUrl"])

    except Exception as e:
        print("create_version_info: " + str(e))
        return False

    return True


def try_get_latest_version():
    """
    尝试获取执行resID的最新的版本信息,用于和即将上传的做比较
    :param old_file:
    :return:
    """

    url_path = "http://localhost:8080/api/get_latest_version"

    code, old_file = SERVER_OTHER_ERROR, ""

    try:
        result = do_post(url_path, post_data)
        result_json = json.loads(result)

        if result_json["code"] != 200:
            code = SERVER_OTHER_ERROR

        else:
            if len(result_json["data"]) == 0:
                code = SERVER_NOT_THIS_RES

            else:
                server_version = result_json["data"][0]["resVersion"]
                if server_version >= base_version_info["resVersion"]:
                    print("server_version=====> " + result_json["data"][0]["resID"] + ": " + server_version)
                    code = SERVER_IS_LATEST
                else:
                    code = SERVER_NEED_UPLOAD
                    old_file = result_json["data"][0]["fullUrl"]

    except Exception as e:
        print(e)
        code, old_file = SERVER_OTHER_ERROR, ""

    return code, old_file


def do_post(url_path, data_json):
    """
    执行http的post请求
    :param url:
    :param post_data:
    :return:
    """
    ret = requests.post(url_path, data=json.dumps(data_json))
    return ret.text


def do_get(url_path):
    """
    执行http的get请求
    :param url:
    :return:
    """
    ret = requests.get(url_path)
    return ret.text


def do_main():
    old_file = ""
    state, old_file = try_get_latest_version()
    if state == SERVER_OTHER_ERROR:
        print("SERVER_OTHER_ERROR!!!!!.")
        return
    elif state == SERVER_IS_LATEST:
        print("SERVER_IS_LATEST!!!!!.")
        return

    upload_package_file(old_file)


if __name__ == '__main__':
    # if get_zippath():
    #     pass
    do_main()





# "resInfos": [
#   {
#     "state": 0,
#     "resID": "login"
#   }
# ]
#
# "resInfos": []
#
# "resInfos": [
#   {
#     "diffMd5": "45217d0f79ce7bd18b2e7e26466bfce8",
#     "fullUrl": "http://10.242.27.37:8000/test/login_20160703.zip",
#     "state": 1,
#     "diffUrl": "http://10.242.27.37:8000/test/login.diff",
#     "userData": {
#       "domains": [
#         "m.kaola.com"
#       ]
#     },
#     "resVersion": "20160703",
#     "resID": "login",
#     "fullMd5": "167ba73e342d67ee9549664dc82adaa9"
#   }
# ]


# [
#     {
# 	      "diffMd5": "45217d0f79ce7bd18b2e7e26466bfce8",
# 	      "appID": "kaola",
# 	      "domain": "m.kaola.com",
# 	      "diffUrl": "http://10.242.27.37:8000/test/exit.diff",
# 	      "resVersion": "20160703",
# 	      "fullUrl": "http://10.242.27.37:8000/test/exit_20160703.zip",
# 	      "appVersion": "1.0.0",
# 	      "resID": "exit",
# 	      "fullMd5": "167ba73e342d67ee9549664dc82adaa9"
# 	    }
# ]
