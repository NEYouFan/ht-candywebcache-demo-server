# -*- coding:utf-8 -*-

import sqlite3


class SqLiteCtrl(object):
    """
    数据库操作的基础接口封装
    """
    def __init__(self):
        self.db = r"./res.db"                       # 在当前目录下创建隐藏的db文件

    def drop_table(self, drp_tb_sql):
        """

        :return:
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        cur.execute(drp_tb_sql)

        con.commit()

        cur.close()
        con.close()

    def create_table(self, crt_tb_sql):
        """
        对DB中的表versionInfo进行重设处理,仅在重设的时候被调用
        :return:
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        cur.execute(crt_tb_sql)

        con.commit()

        cur.close()
        con.close()

    def do_insert(self, insert_sql, params_tuples):
        """
        insert操作
        :param insert_sql: insert操作的sql语句
        :param params_tuples: [(), (), (), ......]      待插入的参数元组列表
        :return:
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        for one in params_tuples:
            cur.execute(insert_sql, one)

        con.commit()

        cur.close()
        con.close()
        return

    def do_select(self, select_sql):
        """
        根据执行的sql语句执行select操作
        :param select_sql:
        :return:
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        cur.execute(select_sql)

        date_set = cur.fetchall()

        cur.close()
        con.close()
        return date_set


class VersionInfoTable(object):
    """
    业务表相关的处理
    """
    table_name = "versionInfo"

    appID = "appID"
    appVersion = "appVersion"
    resID = "resID"
    resVersion = "resVersion"
    diffUrl = "diffUrl"
    diffMd5 = "diffMd5"
    fullUrl = "fullUrl"
    fullMd5 = "fullMd5"
    domain = "domain"

    fields = ("id", appID, appVersion, resID, resVersion, diffUrl, diffMd5, fullUrl, fullMd5, domain)

    drp_tb_sql = "drop table if exists versionInfo"
    crt_tb_sql = """
                create table if not exists versionInfo(
                  id integer primary key autoincrement unique not null,
                  appID varchar(128),
                  appVersion varchar(128),
                  resID varchar(128),
                  resVersion varchar(128),
                  diffUrl varchar(128),
                  diffMd5 varchar(128),
                  fullUrl varchar(128),
                  fullMd5 varchar(128),
                  domain varchar(256)
                );
                """

    insert_sql = "insert into versionInfo " \
                     "(appID, appVersion, resID, resVersion, diffUrl, diffMd5, fullUrl, fullMd5, domain) " \
                     "values (?, ?, ?, ?, ?, ?, ?, ?, ?)"                   # ?为占位符

    select_all_sql = "select * from versionInfo"

    db_sqlite = SqLiteCtrl()

    ORDER_KEY = "ORDER_KEY"
    ORDER_TYPE = "ORDER_TYPE"
    LIMIT = "LIMIT"

    def __init__(self):
        self.order_key = ""
        self.order_type = ""
        self.limit = 0

    def drop_table(self):
        self.db_sqlite.drop_table(self.drp_tb_sql)
        return

    def create_table(self):
        """
        创建表信息
        :return:
        """
        self.db_sqlite.create_table(self.crt_tb_sql)
        return

    def add_new_versions(self, new_versions):
        """
        向表中增加version数据信息
        :return:
        """
        insert_params = []
        for one in new_versions:
            insert_params.append((one[self.appID], one[self.appVersion], one[self.resID], one[self.resVersion],
                                  one[self.diffUrl], one[self.diffMd5], one[self.fullUrl], one[self.fullMd5],
                                  one[self.domain]))
        self.db_sqlite.do_insert(self.insert_sql, insert_params)
        return

    def get_latest_version(self, *args, **kw):
        """
        查询表中的version信息,查询最新版本的信息
        :param args:
        :param kw:
        :return:
        说明:排序/limit部分其实可以采用对象式编程实现的,但是时间来不及了,先这样吧.
        """

        # select部分
        select_part = "select "
        if len(args) == 0:
            select_part += "* "
        else:
            for one in args:
                select_part = select_part + one + ", "

            select_part = select_part[:-2]

        # where部分
        where_part = ""
        if len(kw):
            for (k, v) in kw.items():
                if k == self.ORDER_KEY:
                    self.order_key = v
                elif k == self.ORDER_TYPE:
                    self.order_type = v
                elif k == self.LIMIT:
                    self.limit = v
                elif 'tuple' in str(type(v)):
                    where_part += k + " in " + str(v) + " and "
                else:
                    where_part += k + "='" + v + "' and "

            where_part = "where " + where_part[:-4]

        # 连接起来
        select_sql = select_part + " from " + self.table_name + " " + where_part

        if len(self.order_key):
            select_sql += " order by " + self.order_key
        if len(self.order_type):
            select_sql += " " + self.order_type
        if self.limit:
            select_sql += " limit " + str(self.limit)

        print(select_sql)

        date_set = self.db_sqlite.do_select(select_sql)

        # 将结果取出
        result = []
        for one in date_set:
            if len(args):
                result_item = {}
                for idx in range(len(args)):
                    result_item[args[idx]] = one[idx]

                result.append(result_item)
            else:
                result_item = {}
                for idx in range(len(self.fields)):
                    result_item[self.fields[idx]] = one[idx]

                result.append(result_item)

        return result

    def get_versions(self, *args, **kw):
        """
        查询表中的version信息
        :param args:
        :param kw:
        :return:
        select_all_sql = "select * from versionInfo"
        """
        # select部分
        select_part = "select "
        if len(args) == 0:
            select_part += "* "
        else:
            for one in args:
                select_part = select_part + one + ", "

            select_part = select_part[:-2]

        # where部分
        where_part = ""
        if len(kw):
            for (k, v) in kw.items():
                if 'tuple' in str(type(v)):
                    where_part += k + " in " + str(v) + " and "
                else:
                    where_part += k + "='" + v + "' and "

            where_part = "where " + where_part[:-4]

        # 连接起来
        select_sql = select_part + " from " + self.table_name + " " + where_part

        date_set = self.db_sqlite.do_select(select_sql)

        # 将结果取出
        result = []
        for one in date_set:
            if len(args):
                result_item = {}
                for idx in range(len(args)):
                    result_item[args[idx]] = one[idx]

                result.append(result_item)
            else:
                result_item = {}
                for idx in range(len(self.fields)):
                    result_item[self.fields[idx]] = one[idx]

                result.append(result_item)

        return result


if __name__ == "__main__":
    version_table = VersionInfoTable()
    version_table.create_table()
    # version_table.get_versions(appID="kaola")
    # version_table.get_versions(appID=("kaola", "kaola11"))
    # version_table.get_versions(VersionInfoTable.appVersion, appID=("kaola", "kaola11"), appVersion="1.0.0")
    # version_table.get_versions()
    #
    # new_versions = []
    # version_table.add_new_versions(new_versions)

    result = VersionInfoTable().get_latest_version(appID="kaola", resID="login",
                                                   ORDER_KEY="resVersion", ORDER_TYPE="DESC", LIMIT=1)

    result = version_table.get_versions()
    print(result)










