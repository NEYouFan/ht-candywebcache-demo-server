# -*- coding:utf-8 -*-

# 1. 完成http模块；
# 2. 完成DB模块；
# 	- SQL操作；
# 	- 检测sqllite存在性，并提示对应的信息（安装sqllite、启动sqllite server等）
# 	- 检测表的存在，并提示对应信息（创建表等信息）
# 3. 完成逻辑模块；
# 4. 诊断模块
# 	- 提供DB中version信息查询的处理功能

# http server实现功能包括:
# 1. 实现check_version的两个方式的post请求处理
# 2. 资源包的上传处理
# 3. 诊断模块的get处理

import sys
import http.server
import socketserver
import getopt
import json

from db import VersionInfoTable


CODE_OK = 200                    # 请求成功响应
CODE_PROTOCOL_INVALID = 401      # 协议版本不支持
CODE_APP_ID_INVALID = 402        # appID不支持
CODE_SERVER_ERROR = 501          # 服务器错误
CODE_OTHER_ERROR = 601           # 其他错误

STATE_IS_LATEST = 0              # 提示本地资源已经是最新
STATE_NEED_UPDATE = 1            # 提示需要更新
STATE_NOT_THIS_RES = 2           # 请求资源不存在
STATE_AUTO_RES = 3               # 自动补全的资源信息,请求中未携带资源信息


class VersionCheck(object):

    resID = "resID"
    resVersion = "resVersion"

    """
    必填项,放在功能函数构造的时候
    """
    def __init__(self, version, appID, appVersion, platform):
        self.version = version
        self.app_id = appID
        self.app_version = appVersion
        self.platform = platform

        self.res_infos = []
        self.id_diff = False
        self.auto_fill = False

        self.res_latest_version = {}

    def set_option(self, resInfos, isDiff, autoFill):
        self.res_infos = resInfos
        self.id_diff = isDiff
        self.auto_fill = autoFill

    def all_res_version(self):
        """
        检查appid是否存在
        """
        result = VersionInfoTable().get_versions("resID", "resVersion", appID=self.app_id)
        if len(result) == 0:
            return False
        else:
            for one in result:
                try:
                    if self.res_latest_version[one["resID"]] < one["resVersion"]:
                        self.res_latest_version[one["resID"]] = one["resVersion"]
                except:
                    self.res_latest_version[one["resID"]] = one["resVersion"]        # 第一次,那么就讲version赋值过去作为key的value

            return True

    def deal_noinput_res(self):
        """
        没有传入res的,补全全部的latest version的res资源
        :return:
        """
        res_json = {"resInfos": []}

        if self.auto_fill:
            for k,v in self.res_latest_version.items():
                result = VersionInfoTable().get_versions(appID=self.app_id, resID=k, resVersion=v)

                for one_result in result:
                    one_item = {}
                    one_item[VersionInfoTable.resID] = one_result[VersionInfoTable.resID]
                    one_item[VersionInfoTable.resVersion] = one_result[VersionInfoTable.resVersion]
                    one_item[VersionInfoTable.fullUrl] = one_result[VersionInfoTable.fullUrl]
                    one_item[VersionInfoTable.fullMd5] = one_result[VersionInfoTable.fullMd5]

                    one_item["state"] = 3
                    domains = one_result[VersionInfoTable.domain].split(",")
                    one_item["userData"] = json.dumps({"domains": domains})

                    res_json["resInfos"].append(one_item)
        else:
            pass

        return res_json

    def deal_withinput_res(self):
        """
        有传入res的处理方式
        :return:
        """
        code = CODE_OK
        code_msg = "OK"
        res_json = {"resInfos": []}
        no_the_res = False

        # 先查找传入res的
        for input_one in self.res_infos:
            try:
                tmp_resID = input_one[self.resID]
                input_one[self.resVersion]

                if tmp_resID in self.res_latest_version:
                    self.res_latest_version.pop(tmp_resID)
                else:
                    no_the_res = True

            except Exception as e:
                continue

            one_item = {}

            result = VersionInfoTable().get_latest_version(appID=self.app_id, resID=input_one[self.resID],
                                                           ORDER_KEY="resVersion", ORDER_TYPE="DESC", LIMIT=1)
            if len(result) == 0:
                one_item["state"] = 2
                one_item[VersionInfoTable.resID] = input_one[self.resID]
            else:
                for result_one in result:
                    if result_one[VersionInfoTable.resVersion] == input_one[self.resVersion]:
                        one_item["state"] = 0
                        one_item[VersionInfoTable.resID] = input_one[self.resID]
                        break

                    elif result_one[VersionInfoTable.resVersion] > input_one[self.resVersion]:
                        # 否则返回服务端最新的
                        one_item[VersionInfoTable.resID] = result_one[VersionInfoTable.resID]
                        one_item[VersionInfoTable.resVersion] = result_one[VersionInfoTable.resVersion]
                        one_item[VersionInfoTable.fullUrl] = result_one[VersionInfoTable.fullUrl]
                        one_item[VersionInfoTable.fullMd5] = result_one[VersionInfoTable.fullMd5]
                        one_item[VersionInfoTable.diffUrl] = result_one[VersionInfoTable.diffUrl]
                        one_item[VersionInfoTable.diffMd5] = result_one[VersionInfoTable.diffMd5]

                        one_item["state"] = 1
                        domains = result_one[VersionInfoTable.domain].split(",")
                        one_item["userData"] = json.dumps({"domains": domains})
                        break

                    else:
                        # 说明传入的版本是更新的,暂时回复不用更新处理即可
                        one_item["state"] = 0
                        one_item[VersionInfoTable.resID] = input_one[self.resID]
                        break

            res_json["resInfos"].append(one_item)

        # 然后执行需要补全的
        if self.auto_fill:
            for k,v in self.res_latest_version.items():
                result = VersionInfoTable().get_versions(appID=self.app_id, resID=k, resVersion=v)

                for one_result in result:
                    one_item = {}
                    one_item[VersionInfoTable.resID] = one_result[VersionInfoTable.resID]
                    one_item[VersionInfoTable.resVersion] = one_result[VersionInfoTable.resVersion]
                    one_item[VersionInfoTable.fullUrl] = one_result[VersionInfoTable.fullUrl]
                    one_item[VersionInfoTable.fullMd5] = one_result[VersionInfoTable.fullMd5]
                    one_item[VersionInfoTable.diffUrl] = result_one[VersionInfoTable.diffUrl]
                    one_item[VersionInfoTable.diffMd5] = result_one[VersionInfoTable.diffMd5]

                    one_item["state"] = 3
                    domains = one_result[VersionInfoTable.domain].split(",")
                    one_item["userData"] = json.dumps({"domains": domains})

                    res_json["resInfos"].append(one_item)
        else:
            # if no_the_res:
            #     code = CODE_OTHER_ERROR
            #     code_msg = "The Input Res is No In Server"
            pass

        return res_json, code, code_msg


    def do_check(self):
        """
            实际的业务处理
        """
        code = CODE_OK
        code_msg = "OK"

        if len(self.res_infos):
            res_json, code, code_msg = self.deal_withinput_res()
        else:
            res_json = self.deal_noinput_res()

        return res_json, code, code_msg


"""
Http业务处理的模块
"""
class PackageHttpHandler(http.server.BaseHTTPRequestHandler):
    """
    继承BaseHTTPRequestHandler用于http request的自定义处理相关
    """

    """
    get类reques的处理
    """
    def do_GET(self):
        try:
            if self.path in "/api/version_infos":
                self.do_response(CODE_OK, "ok", self.do_get_all_versions_url())

        except Exception as e:
            print("do_GET: "+ str(e))
            self.do_response(CODE_OTHER_ERROR, str(e))

        return

    """
    post类request的处理
    """
    def do_POST(self):
        try:
            if self.path in "/api/version_check/webapp":
                # 指定check version的url的操作
                self.do_checkversion_url()
            elif self.path in "/api/upload_version":
                # 执行版本信息的提交
                self.do_upload_version_url()
            elif self.path in "/api/get_latest_version":
                self.get_latest_version_url()

        except Exception as e:
            print("do_POST" + str(e))
            self.do_response(CODE_OTHER_ERROR, str(e))

        return

    """
    获取http Reques的内容
    """
    def get_content_json(self):
        content_length = int(self.headers["Content-Length"])
        content_str = self.rfile.read(content_length).decode('utf-8')
        content_json = json.loads(content_str)

        return content_json

    """
    返回值的处理
    """
    def do_response(self, code, err_msg, data_json={}):

        res_json = {"code": code, "errMsg": err_msg, "data": data_json}
        res = json.dumps(res_json).encode('utf-8')

        self.protocol_version = 'HTTP/1.1'
        self.send_response(200)
        self.end_headers()
        self.wfile.write(res)

        return

    #############################################################################
    def do_get_all_versions_url(self):
        """
        获取所有的版本信息
        :return:
        """
        res_json = VersionInfoTable().get_versions()
        return res_json

    def do_upload_version_url(self):
        """
        /api/upload_version
        """
        content_json = self.get_content_json()
        new_versions = []
        for one in content_json:
            try:
                one_version = {}
                one_version[VersionInfoTable.appID] = one[VersionInfoTable.appID]
                one_version[VersionInfoTable.appVersion] = one[VersionInfoTable.appVersion]
                one_version[VersionInfoTable.resID] = one[VersionInfoTable.resID]
                one_version[VersionInfoTable.resVersion] = one[VersionInfoTable.resVersion]
                one_version[VersionInfoTable.diffUrl] = one[VersionInfoTable.diffUrl]
                one_version[VersionInfoTable.diffMd5] = one[VersionInfoTable.diffMd5]
                one_version[VersionInfoTable.fullUrl] = one[VersionInfoTable.fullUrl]
                one_version[VersionInfoTable.fullMd5] = one[VersionInfoTable.fullMd5]
                one_version[VersionInfoTable.domain] = one[VersionInfoTable.domain]

                new_versions.append(one_version)
            except Exception as e:
                new_versions = []
                print("do_upload_version: " + str(e))

        VersionInfoTable().add_new_versions(new_versions)

        res_json = {"insert_cnt": len(new_versions)}

        self.do_response(CODE_OK, "ok", res_json)
        return

    def get_latest_version_url(self):
        """
        /api/get_latest_version
        :return:
        """
        content_json = self.get_content_json()
        latest_versions = []

        try:
            appID = content_json["appID"]
            resID = content_json["resID"]

            result = VersionInfoTable().get_latest_version(appID=appID, resID=resID,
                                                           ORDER_KEY="resVersion", ORDER_TYPE="DESC", LIMIT=1)
            for one in result:
                one_item = {}
                one_item[VersionInfoTable.resID] = one[VersionInfoTable.resID]
                one_item[VersionInfoTable.resVersion] = one[VersionInfoTable.resVersion]
                one_item[VersionInfoTable.fullUrl] = one[VersionInfoTable.fullUrl]
                one_item[VersionInfoTable.fullMd5] = one[VersionInfoTable.fullMd5]
                one_item[VersionInfoTable.diffUrl] = one[VersionInfoTable.diffUrl]
                one_item[VersionInfoTable.diffMd5] = one[VersionInfoTable.diffMd5]
                latest_versions.append(one_item)

        except Exception as e:
            print("get_latest_version_url: " + str(e))
            self.do_response(CODE_OTHER_ERROR, "get latest version error.")
            return

        self.do_response(CODE_OK, "ok", latest_versions)
        return

    def do_checkversion_url(self):
        """
        /api/version_check/webapp
        """
        content_json = self.get_content_json()

        # 必选项
        version = content_json["version"]
        appID = content_json["appID"]
        appVersion = content_json["appVersion"]
        platform = content_json["platform"]

        resInfos = []
        isDiff = False
        autoFill = False
        try:
            # 可选项
            resInfos = content_json["resInfos"]
            # resInfos = json.JSONDecoder().decode(tmp)
        except Exception as e:
            print("resInfos: " + str(e))
        try:
            isDiff = bool(content_json['isDiff'])
        except Exception as e:
            print("isDiff: " + str(e))
        try:
            autoFill = bool(content_json["autoFill"])
        except Exception as e:
            print("autoFill: " + str(e))

        # 准备执行业务处理
        check_version = VersionCheck(version, appID, appVersion, platform)
        check_version.set_option(resInfos, isDiff, autoFill)

        if check_version.all_res_version():
            res_json, code, code_msg = check_version.do_check()
            self.do_response(code, code_msg, res_json)
        else:
            self.do_response(CODE_APP_ID_INVALID, "The appID is invalid.")
        return


class Server(object):
    """
    服务类
    """
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 8080
        self.is_clear = False

    def get_args(self):
        """
        服务执行的方式为:script -h host -p port
        :return:
        """
        try:
            opt_list, args = getopt.getopt(sys.argv[1: ], "h: p: ")
            for opt, value in opt_list:
                if opt == '-h':
                    self.host = value
                elif opt == '-p':
                    self.port == int(value)
                elif opt == '-c':
                    self.is_clear = True
                else:
                    print("Usage:\tscript [-h host] [-p port] [-c]\n"
                          "      \t-c\t\tclear db table")
        except getopt.GetoptError as e:
            print(str(e))

    def run(self):
        """
        启动服务并执行
        :return:
        """
        self.get_args()

        if self.is_clear:
            VersionInfoTable().drop_table()

        VersionInfoTable().create_table()

        http_server = socketserver.TCPServer((self.host, self.port), PackageHttpHandler)

        http_server.serve_forever()

        return


if __name__ == "__main__":
    server = Server()
    print('Start demo server on %s port %d' % (server.host, server.port))
    server.run()
