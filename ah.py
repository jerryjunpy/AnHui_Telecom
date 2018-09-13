#!/usr/bin/python
# -*- coding: utf-8 -*-
import random
import requests.utils
import jsonpath
from lxml import etree
import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
import execjs
from AnHui.js import CRYPTO_JS
import calendar
import time
from scrapy import Selector

"""
登录有加密
获取通话记录加密
获取下一页通话记录参数加密
"""


class AH:
    """
    pc网页版安徽电信
    """

    def __init__(self, account, password):

        self.session = requests.session()
        self.account = account
        self.password = password
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/66.0.3359.181 Safari/537.36",
            "Host": "ah.189.cn",
            "Origin": "http://ah.189.cn",
        }
        self.js_ctx = execjs.compile(CRYPTO_JS)

    def check_is_login(self):
        """
        获取验证码，并登陆
        :return:
        """
        VImage_url = 'http://ah.189.cn/sso/VImage.servlet?random=' + str(random.random())

        Validate_url = 'http://ah.189.cn/sso/ValidateRandom'
        VImage_res = self.session.get(VImage_url)
        with open("captcha.jpg", "wb") as f:
            f.write(VImage_res.content)
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            print('到本地目录打开captcha.jpg获取验证码')

        finally:
            captcha = input('please input the captcha:')

        self.session.headers.update({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        data = {"validCode": captcha}
        Validate_res = self.session.post(Validate_url, data=data)
        Validate_j = Validate_res.json()

        if Validate_j.get('flage'):

            login_url = 'http://ah.189.cn/sso/LoginServlet'

            password = self.js_ctx.call("k", self.password)

            login_data = {
                "loginType": "4",
                "accountType": "9",
                "loginName": self.account,
                "latnId": "",
                "passType": "0",
                "passWord": password,
                "validCode": captcha,
                "csrftoken": "",
                "ssoAuth": "0",
                "returnUrl": "/service/account/init.action",
                "sysId": " 1003",
            }
            try:
                login_res = self.session.post(login_url, data=login_data)
                login_text = login_res.text
                j = etree.HTML(login_text)
                name = j.xpath('.//div[@class="welcome_info bd8"]//div[@id="custInfo"]/div[@class="fl"]/text()')[
                    0].strip()
                print(name)
            except Exception as e:
                print(e)
                print("登录失败")
                return self.check_is_login()

            else:
                return True
        else:
            print("验证码错误，重新输入")
            return self.check_is_login()

    def used_balance(self):
        """
        用户余额和当月账单
        :return:
        """

        used_balance_url = 'http://ah.189.cn/service/account/usedBalance.action'
        used_balance_data = {
            "serviceNum": self.account
        }

        try:
            used_balance_res = self.session.post(used_balance_url, data=used_balance_data)
            used_balance_j = used_balance_res.json()
        except Exception as e:
            print(e)

        else:
            curFee = jsonpath.jsonpath(used_balance_j, "$..left_balance")[0]
            curFeeTotal = jsonpath.jsonpath(used_balance_j, "$..can_use_balance")[0]
            billFee = jsonpath.jsonpath(used_balance_j, "$..consume_fee")[0]
            print("当前实际余额{}".format(curFee))
            print("专有账户余额，储蓄余额{}".format(curFeeTotal))
            print("当月消费{}".format(billFee))

            # 当月账单
            month = datetime.datetime.now().strftime("%Y%m")  # 当前月份
            billStartDate = month + '01'  # 账单开始日期
            billEndDate = datetime.date.today().strftime("%Y%m%d")  # 当月账单结束日期
            print(billStartDate, billEndDate)

    def query_account_list(self):
        """
        入网时间，用户id
        :return:
        """

        query_account_url = 'http://ah.189.cn/service/custInfo/queryAccountList.action'

        try:
            query_account_res = self.session.post(query_account_url)
            query_account_j = query_account_res.json()
            print(query_account_j)
            inNetTime = jsonpath.jsonpath(query_account_j, "$..createDate")[0][:10]
            authorizeId = jsonpath.jsonpath(query_account_j, "$..cust_id")[0]
            print(inNetTime, authorizeId)
            net_age_days = (datetime.datetime.now() - datetime.datetime.strptime(inNetTime, "%Y-%m-%d")).days

            netAge = (lambda x: "{}年{}个月".format(x // 365, x % 365 // 30) if x // 365 > 0 else "{}个月".format(
                x % 365 // 30))(net_age_days)
            # 转换成多少年多少天格式
            print("网龄{}".format(netAge))

        except Exception as e:
            print(e)

    def cust_info(self):
        """
        联系人电话
        :return:
        """

        info_url = 'http://ah.189.cn/service/manage/showCustInfo.action'

        try:
            info_res = self.session.get(url=info_url)
            info_text = info_res.text
            info_html = etree.HTML(info_text)
            regAddress = info_html.xpath(
                './/div[@class="main-wrap"]//div[@class="description"]/div[1]//ul/li[2]/text()')  # 所在城市
            contactNum = info_html.xpath(
                './/div[@class="main-wrap"]//div[@class="description"]/div[2]//ul/li[7]/text()')  # 联系人电话
            email = info_html.xpath(
                './/div[@class="main-wrap"]//div[@class="description"]/div[2]//ul/li[8]/text()')  # 电子邮箱
            customerSex = info_html.xpath(
                './/div[@class="main-wrap"]//div[@class="description"]/div[2]//ul/li[5]/text()')  # 性别

        except Exception as e:
            print(e)
            pass

        else:
            print(regAddress[1].replace('\r\n', ''))
            print(contactNum[1].replace('\r', ''))
            print(email[1].replace('\r\n', ''))
            print(customerSex[1].replace('\r\n', ''))

    def half_year_acount(self):
        """
        获取月账单
        :return:
        """

        half_year_url = 'http://ah.189.cn/service/personal/halfYearAcount.action'

        data = {"serviceNum": self.account}
        try:

            response = self.session.post(url=half_year_url, data=data)

            if response.status_code == 200:
                half_year_j = response.json()
                month_list = half_year_j.get("data").split(',')

        except Exception as e:

            print('获取月账单失败,重新获取')
            return self.half_year_acount()

        else:
            for i in range(6):
                year = month_list[i][:4]
                month = month_list[i][-2:]
                billStartDate = month_list[i] + '01'  # 账单开始日期

                billEndDate = month_list[i] + str(calendar.monthrange(int(year), int(month))[1])  # 结束日期
                billFee = month_list[i + 6]  # 本月消费

                print({
                    "billStartDate": billStartDate,
                    "billEndDate": billEndDate,
                    "billFee": billFee.replace('#', '')
                })

    def phoneAndInternetDetail(self):
        """
        :return:macCode
        """

        self.session.headers.update(
            {"Referer": "http://ah.189.cn/service/bill/fee.action?type=phoneAndInternetDetail"})  # 会验证refere
        detail_url = 'http://ah.189.cn/service/bill/phoneAndInternetDetail.action?rnd=' + str(random.random())

        try:
            detail_res = self.session.get(detail_url)
            if detail_res.status_code == 200:
                detail_html = etree.HTML(detail_res.text)

                macCode = detail_html.xpath(".//div[@id='wireless']//input[@id='macCode']/@value")[0]

                return macCode

        except Exception as e:
            print(e)
            return self.phoneAndInternetDetail()

    def selfservice_bill(self, macCode):
        """
        获取通讯详单短信验证码并获取通信详单
        :param macCode:
        :return:
        """
        sendBillSms_url = 'http://ah.189.cn/service/bill/sendValidReq.action'

        for _ in range(0, 6):  # 最近半年

            if _ == 0:

                month = datetime.datetime.now().strftime("%Y-%m")
                begDate = month + '-01'  # 开始日期

                endDate = datetime.date.today().strftime("%Y-%m-%d")  # 当天的日期



            else:
                last = datetime.date.today() - relativedelta(months=+_)

                month = last.strftime("%Y-%m")
                begDate = month + '-01'  # 开始日期

                endDate = month + '-' + str(calendar.monthrange(last.year, last.month)[1])  # 结束日期

            _key = self.account[1:2] + self.account[3:4] + self.account[6:7] + self.account[8:10]
            params = "mobileNum=" + self.account + "&key=" + _key  # 加密前的参数
            v = self.js_ctx.call("k", params)

            sendBillSms_data = {"_v": v}

            try:
                time.sleep(60)  # 短信验证不能频繁发送，需等待一分钟
                sendBillSms_res = self.session.post(sendBillSms_url, data=sendBillSms_data)

                if sendBillSms_res.status_code == 200:

                    checkBillSms_j = sendBillSms_res.json()

                    if checkBillSms_j.get("success"):

                        code = input('请输入查询通话详单的短信验证码:')

                        # 开始获取通话详单

                        checkBillSms_url = "http://ah.189.cn/service/bill/feeDetailrecordList.action"

                        params = "currentPage=&pageSize=10&effDate=" + begDate + "&expDate=" + endDate + \
                                 "&serviceNbr=" + self.account + "&operListID=" + "2" + \
                                 "&isPrepay=" + "1" + "&pOffrType=481&random=" + code \
                                 + "&macCode=" + macCode

                        feeDetailrecordList_v = self.js_ctx.call("k", params)

                        checkBillSms_data = {"_v": feeDetailrecordList_v}

                        checkBillSms_res = self.session.post(url=checkBillSms_url, data=checkBillSms_data)

                        checkBillSms_j = checkBillSms_res.text

                        ml = etree.HTML(checkBillSms_j)

                        recoders = ml.xpath(".//table[@class='tabsty']//input[@id='totalRow']/@value")[0]  # 通话记录条数
                        fileName = ml.xpath(".//table[@class='tabsty']//input[@id='fileName']/@value")[0]  # 下一页请求的参数
                        recoders = int(recoders)

                        if recoders > 1:

                            pages = (recoders // 10 if recoders % 10 == 0 else recoders // 10 + 1)

                            Searchresult = ml.xpath(".//table[@class='tabsty']/tbody/tr")

                            for i in Searchresult:
                                commMode = i.xpath("./td[2]/nobr/text()")[0]

                                x = commMode.find('总计')  # 去掉最后一条统计记录

                                if x < 0:
                                    commType = i.xpath("./td[3]/nobr/text()")[0]

                                    commPlac = i.xpath("./td[4]/nobr/text()")[0]

                                    anotherNm = i.xpath("./td[5]/nobr/text()")[0]

                                    startTime = i.xpath("./td[7]/nobr/text()")[0]

                                    commTime = i.xpath("./td[8]/nobr/text()")[0]

                                    commFee = i.xpath("./td[9]/nobr/text()")[0]

                                    TXXiangDanModel = {
                                        "commMode": commMode.strip(),
                                        "commType": commType.strip(),
                                        "commPlac": commPlac.strip(),
                                        "anotherNm": anotherNm.strip(),
                                        "startTime": startTime.strip(),
                                        "commTime": commTime.strip(),
                                        "commFee": commFee.strip()
                                    }
                                    print(TXXiangDanModel)

                            if pages > 1:  # 下一页通话记录
                                self.second_selfservice(pages, fileName, macCode, begDate, endDate)

                        else:
                            print("{}：无通话记录".format(begDate[:7]))
                    else:
                        print("短信验证获取失败")

            except Exception as e:
                print(e)

    def second_selfservice(self, pages, filename, macCode, begDate, endDate):
        """
        下一页的通话记录，加密参数结构和首页不一样
        :param pages: 页码
        :param filename: 文件名
        :param macCode:
        :param begDate:
        :param endDate:
        :return:
        """

        checkBillSms_url = "http://ah.189.cn/service/bill/feeDetailrecordList.action"

        for pageNo in range(1, pages):

            parms = "currentPage=" + str(pageNo + 1) + "&pageSize=10&effDate=" + begDate + "&expDate=" + endDate + \
                    "&serviceNbr=" + self.account + "&operListID=" + "2" + "&isPrepay=" + "1" + \
                    "&pOffrType=" + "481" + "&fileName=" + filename + "&macCode=" + macCode

            feeDetailrecordList_v = self.js_ctx.call("k", parms)

            checkBillSms_data = {"_v": feeDetailrecordList_v}

            checkBillSms_res = self.session.post(url=checkBillSms_url, data=checkBillSms_data)

            checkBillSms_j = checkBillSms_res.text

            ml = etree.HTML(checkBillSms_j)

            Searchresult = ml.xpath(".//table[@class='tabsty']/tbody/tr")

            for i in Searchresult:
                commMode = i.xpath("./td[2]/nobr/text()")[0]

                x = commMode.find('总计')

                if x < 0:
                    commType = i.xpath("./td[3]/nobr/text()")[0]

                    commPlac = i.xpath("./td[4]/nobr/text()")[0]

                    anotherNm = i.xpath("./td[5]/nobr/text()")[0]

                    startTime = i.xpath("./td[7]/nobr/text()")[0]

                    commTime = i.xpath("./td[8]/nobr/text()")[0]

                    commFee = i.xpath("./td[9]/nobr/text()")[0]

                    TXXiangDanModel = {
                        "commMode": commMode.strip(),
                        "commType": commType.strip(),
                        "commPlac": commPlac.strip(),
                        "anotherNm": anotherNm.strip(),
                        "startTime": startTime.strip(),
                        "commTime": commTime.strip(),
                        "commFee": commFee.strip()
                    }
                    print(TXXiangDanModel)

def main():
    phone_number = ""
    service_password = ""
    ah = AH(phone_number, service_password)
    if ah.check_is_login():
        macCode = ah.phoneAndInternetDetail()
        if macCode:
            ah.selfservice_bill(macCode)
            ah.used_balance()
            ah.query_account_list()
            ah.cust_info()
            ah.half_year_acount()

if __name__ == "__main__":
    main()
