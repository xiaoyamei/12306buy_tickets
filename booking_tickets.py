"""
    产品描述：通过12306预订火车票（需要人为输入验证码然后点击登录；车票预定成功后需要人为付款）
    作者: 小丫
    版本：V1.1
    日期：2018-12-29
    功能：
       1、支持为多人购票：用户提供乘客列表（乘客需为账号下包含的乘客）
       2、支持提供车次选择范围：用户提供车次列表，以增加订票成功的机率。
       3、支持提供席别选择范围：用户提供席别列表，以增加订票成功的机率。
       4、指定的车次和席别无车票时，支持循环刷票。
       5、你也可以不指定车次和席别，程序会为你预订任意车次的默认席别。
       6、预订成功后可自动播放音乐。
    新增功能：在提交订单方法（submitOrder）中，把等待时间由写死的sleep时间改为实际判断是否满足条件。
"""
import time, subprocess, logging, re, os
from selenium import webdriver
from selenium.webdriver.support.select import Select
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s-%(levelname)s-%(message)s")
logging.disable(logging.INFO)

# 在余票查询页面的出发站和目的站输入框中添加的cookies字典，更多城市的cookies信息根据需要自己添加
CityCookies = {"北京": "%u5317%u4EAC%2CBJP", "上海": "%u4E0A%u6D77%2CSHH", "天津": "%u5929%u6D25%2CTJP", "西安": "%u897F%u5B89%2CXAY",
               "重庆": "%u91CD%u5E86%2CCQW", "长沙": "%u957F%u6C99%2CCSQ", "长春": "%u957F%u6625%2CCCT", "成都": "%u6210%u90FD%2CCDW",
               "深圳": "%u6DF1%u5733%2CSZQ", "杭州": "%u676D%u5DDE%2CHZH", "广州": "%u5E7F%u5DDE%2CGZQ", "福州": "%u798F%u5DDE%2CFZS",
               "南京": "%u5357%u4EAC%2CNJH", "石家庄": "%u77F3%u5BB6%u5E84%2CSJP", "合肥": "%u5408%u80A5%2CHFH",
               "昆明": "%u6606%u660E%2CKMM", "银川": "%u94F6%u5DDD%2CYIJ", "武汉": "%u6B66%u6C49%2CWHN", "西宁": "%u897F%u5B81%2CXNO",
               "厦门": "%u897F%u5B81%2CXNO", "南充": "%u5357%u5145%2CNCW", "安康": "	%u5B89%u5EB7%2CAKY"}

class BookTickets(object):
    """
        进行订票相关操作、如登录、查询、预定、选择乘客等。
    """
    def __init__(self, usrName, pw, startStation, endStation, dtime, trainNumber, passengers, seatClass):
        """
            构造函数：初始化各变量
        """
        self.usrName = usrName                  # 用户名、登录名
        self.password = pw                      # 密码
        self.startStation = startStation        # 出发站
        self.endStation = endStation            # 目的站
        self.dtime = dtime                      # 日期
        self.trainNumber = trainNumber          # 车次， 为空字符串时表示所有车次
        self.passengers = passengers            # 乘客列表
        self.seatClass = seatClass              # 席位类别

        self.loginUrl = "https://kyfw.12306.cn/otn/login/init"              # 登录url
        self.loginOkUrl = "https://kyfw.12306.cn/otn/view/index.html"       # 登录成功后自动跳转至的页面
        self.queryUrl = "https://kyfw.12306.cn/otn/leftTicket/init"         # 余票查询页面的url
        self.choosePassengersUrl = "https://kyfw.12306.cn/otn/confirmPassenger/initDc"       # 点击预定按钮后进入选择乘客页面
        self.errorUrl = "https://www.12306.cn/mormhweb/logFiles/error.html"      # 出错的url
        self.payUrl1 = "https://kyfw.12306.cn/otn//payOrder/init"           # 付款页面可能的url
        self.payUrl2 = "https://kyfw.12306.cn/otn/view/train_order.html"    # 付款页面可能的url

        self.driver = webdriver.Firefox()       # 实例化浏览器窗口
        self.implicitly_wait_tm = 7             # 隐形等待时间
        self.refresh_tm = 2                     # 刷票频率：sleep几秒后再查询余票

    def login(self):
        """
            登录12306
        """
        print("\n**********开始登录12306**********", datetime.now())
        self.driver.implicitly_wait(self.implicitly_wait_tm)         # 设置隐形等待时间
        self.driver.maximize_window()           # 最大化浏览器窗口
        self.driver.get(self.loginUrl)          # 访问登录页面
        self.driver.find_element_by_id("username").send_keys(self.usrName)      # 输入用户名
        self.driver.find_element_by_id("password").send_keys(self.password)     # 输入密码
        print("请在浏览器上输入验证码......")

        while self.driver.current_url != self.loginOkUrl:       # 不断循环以判断是否登录成功，登录成功则退出循环
            if self.driver.current_url == self.errorUrl:
                print("登录出错！", datetime.now())
                exit(1)
            else:
                time.sleep(1)

        print("登录成功！", datetime.now())

    def addCookies(self):
        """
            添加必要的cookies。
        """
        print("\n**********开始添加必要的cookies**********", datetime.now())
        self.driver.get(self.queryUrl)      # 访问余票查询页面
        # 以下cookies必须添，否则无法正常查询车票
        self.driver.add_cookie({"name": "_jc_save_fromStation", "value": CityCookies[self.startStation]})       # 出发站cookies
        self.driver.add_cookie({"name": "_jc_save_toStation", "value": CityCookies[self.endStation]})           # 目的站cookies
        self.driver.add_cookie({"name": "_jc_save_fromDate", "value": self.dtime})                      # 日期cookies
        self.driver.refresh()       # 添加cookies后要重新刷新网页，否则新添的cookies相当于没生效
        print("cookies组装完成！", datetime.now())

    def choosePassengers(self):
        """
            选择乘客
        """
        print("\n**********开始选择乘客**********", datetime.now())
        for i in self.passengers:
            print("开始选择乘客：{}".format(i), datetime.now())
            try:
                self.driver.find_element_by_xpath("//label[text()='{}']".format(i)).click()     # 勾选乘客名称对应的复选框
                print("乘客{}选择成功".format(i), datetime.now())
            except Exception as e:
                print(e, datetime.now())

    def chooseSeat(self):
        """
            选座：只有高铁才支持选座: 后续完善
        """
        pass

    def chooseSeatClass(self):
        """
            选择席别（G：二等座、一等座、商务座； T：硬卧、硬座、软卧、高级软卧；特等座、动卧、软座)
            对所有指定的乘客，按照提供的席别列表，选择席别。
            选择成功返回True（表示可以直接点击提交按钮）,选择失败返回False（表示需要返回余票查询页面进行查询和预订）.
        """
        # 席别与value的对应关系，用以选择席别用
        self.seatClassValue = {"硬座": "1", "硬卧": "3", "软卧": "4", "高级软卧": "6", "一等座": "M", "二等座": "0", "商务座": "9"}
        print("\n**********开始选择席别**********", datetime.now())

        if self.seatClass == []:
            print("没有指定席别，采用默认选择", datetime.now())
            return True     # 返回True，则可以直接点击提交按钮了
        else:               # 如果指定了席别，则走else这条路
            for passengerId in list(range(len(self.passengers))):                          # 遍历所有指定的乘客
                passengerId += 1
                seatType_id = "seatType_" + str(passengerId)                               # 查找乘客的席别控件时要用到的控件id
                self.myselect = Select(self.driver.find_element_by_id(seatType_id))        # 利用选择下拉框创建选择实例

                # 获取可选席别
                seatOpt_raw = list(map(lambda x: x.text, self.myselect.options))        # 获取的席别包含括号
                seatOpt = list(map(lambda x: re.search(u'[\u4e00-\u9fa5]+', x).group(), seatOpt_raw))

                # 获取当前默认席别
                defaultSeat = re.search(u'[\u4e00-\u9fa5]+', self.myselect.all_selected_options[0].text).group()

                logging.info("当前可选席别包括：{}".format(seatOpt))
                logging.info("用户指定的席别包括:{}".format(self.seatClass))
                logging.info("当前系统默认选择的席别：{}".format(defaultSeat))
                flag = False                    # 标记是否选择席别成功

                # self.driver.implicitly_wait(2)
                for i in self.seatClass:        # 遍历用户提供的席别列表
                    if (i in seatOpt) and (i != defaultSeat):            # 如果该席别在可选席别的列表中,且不为默认席别
                        self.myselect.select_by_value(self.seatClassValue[i])
                        print("第{}位乘客{}选择席别为：{}".format(passengerId, self.passengers[passengerId - 1], i), datetime.now())
                        flag = True
                        break
                    elif (i in seatOpt) and (i == defaultSeat):
                        print("第{}位乘客{}选择席别为：{}".format(passengerId, self.passengers[passengerId - 1], i),
                              datetime.now())
                        flag = True
                        break
                    else:
                        logging.info("当前无[{}]席别".format(i))
                        continue
                # self.driver.implicitly_wait(self.implicitly_wait_tm)

                if not flag:
                    return False        # 返回False,需要回到查询页面重新订票
                else:
                    continue

            return True                 # 返回True，则可以直接点击提交按钮了

    def playMusic(self, music):
        """
            播放音乐
        """
        subprocess.Popen(['open', music])


    def submitOrder(self):
        """
            提交订单：包括在选择乘客页面点击提交按钮、在提交后弹出的核对框中点击确认按钮、在进入网上支付页面后提示订单提交完成。
        """
        print("\n**********开始提交订单**********", datetime.now())
        self.driver.find_element_by_id("submitOrder_id").click()        # 点击提交订单按钮, 之后会弹出核对信息框

        # 在核对信息框弹出来后，点击其中的确认按钮
        confirm = self.driver.find_element_by_id("qr_submit_id")
        counter = 0         # 点击确认按钮的计数器
        flag = False
        while not flag:
            if confirm.is_displayed():
                flag = True
            else:
                flag = False
        self.chooseSeat()       # 高铁选座（暂不支持）
        confirm.click()
        counter += 1
        logging.info("在信息核对页面已点击确认按钮{}次".format(counter))

        # 当付款页面出现后，表示订单提交成功
        flag = False
        while not flag:
            url = self.driver.current_url.split("?")[0]
            if url == self.payUrl1 or url == self.payUrl2:
                print("订单提交成功", datetime.now())
                flag = True
            else:
                flag = False
                try:
                    self.driver.find_element_by_id("qr_submit_id").click()
                    counter += 1
                    logging.info("在信息核对页面已点击确认按钮{}次".format(counter))
                except Exception as e:
                    pass

        print("\n**********开始播放提示音乐**********", datetime.now())
        self.playMusic("alarm.wav")         # 播放音乐，提示订单完成。

    def getElemFromTrain(self, train, index):
        """
            获取具体车次的相关元素，如获取某车次的指定席别的元素，或获取某车次的预订按钮元素
            :param train: 车次
            :param index: 获取元素的index数字，为int类型
            :return: 返回定位的元素
        """
        trainUp = train.upper()
        trainElem = self.driver.find_element_by_link_text(trainUp)                                  # 定位车次元素
        self.driver.implicitly_wait(1.5)

        if index != 13:
            targetElem = trainElem.find_element_by_xpath("../../../../../td[{}]".format(index))     # 非13为定位席别元素
        else:
            try:
                targetElem = trainElem.find_element_by_xpath("../../../../../td[{}]/a".format(index))   # 13为定位预订按钮元素
            except:
                targetElem = trainElem.find_element_by_xpath("../../../../../td[{}]".format(index))

        logging.info("根据车次{}和index{}定位到的元素为类型为：{},内容为：{}".format(train, index, targetElem.tag_name, targetElem.text))
        self.driver.implicitly_wait(self.implicitly_wait_tm)
        return targetElem

    def has_tickets(self, train, seatclass):
        """
            判断指定车次是否有指定席别的剩余票，有则返回True,无则返回False
        """
        # 各种席别与html中对应的td顺序，用来查找指定席别是否还有位置
        seatTdOrderDict = {"商务座": 2, "特等座": 2, "一等座": 3, "二等座": 4, "高级软卧": 5, "软卧": 6, "动卧": 7, "硬卧": 8,
                       "软座": 9, "硬座": 10}
        seatclassElem = self.getElemFromTrain(train, seatTdOrderDict[seatclass])  # 找指定车次的指定席别元素
        # 根据席别元素的text内容作出不同处理
        seatclassNumber = seatclassElem.text       # 获取席别剩余数量
        logging.info("{}[{}]的数量为：{}".format(train, seatclass, seatclassNumber))
        if seatclassNumber == "--":
            return False
        elif seatclassNumber == "无":
            return False
        else:
            return True

    def isbookable(self, train):
        """
            判断指定车次的预订按钮是否可用，可用则返回True,不能用则返回False
        """
        self.reserveElem = self.getElemFromTrain(train, 13)     # 获取指定车次的预订按钮
        if self.reserveElem.tag_name != 'a':         # 预订元素是a：表示可以点击的按钮；如果不是a：表示该车次不能预订
            print("车次{}无剩余车票，不能预订！".format(train), datetime.now())
            return False
        else:
            return True

    def getTrainFromReserveBtn(self, elem):
        """
            根据预订按钮元素找车次名称
            :elem: 预订按钮
            :return: 对应的车次名称
        """
        trainElem = elem.find_element_by_xpath("../../td[1]/div/div/div/a")         # 定位车次元素
        trainName = trainElem.text
        return trainName

    def queryAndReserve(self):
        """
            查询及预订
        """
        print("\n**********开始预定车票**********", datetime.now())
        flag = False                                                        # 标记：控制外层循环

        if self.trainNumber == []:                                          # 没有指定具体车次，即任意车次都可以
            count = 0                                                       # 跟踪点击查询按钮都次数
            while self.driver.current_url == self.queryUrl:                 # 当前页面不是查询页面时说明预定成功了，跳出循环
                self.driver.find_element_by_id("query_ticket").click()      # 点击查询按钮，余票查询
                count += 1
                print("点击查询按钮{}次".format(count), datetime.now())
                order = 0                                                   # 跟踪预定的顺序号
                try:
                    self.reserveElems = self.driver.find_elements_by_link_text("预订")     # 找到所有预订按钮，形成列表
                    for i in self.reserveElems:
                        order += 1

                        if self.seatClass == []:           # 如果没有指定席别
                            i.click()                                              # 点击预定按钮
                            print("点击第{}个预定按钮".format(order), datetime.now())
                            flag = True
                            # time.sleep(1)
                            break
                        else:
                            trainName = self.getTrainFromReserveBtn(i)             # 从预订按钮元素获取车次名称
                            for seat in self.seatClass:
                                if self.has_tickets(trainName, seat):              # 如果这趟车次有指定席别
                                    i.click()
                                    print("点击第{}个预定按钮".format(order), datetime.now())
                                    # time.sleep(1)
                                    flag = True
                                    break
                                else:
                                    continue

                            if flag:                                                # 控制外层循环
                                break
                            else:
                                continue

                    if flag:        # 控制最外层的while循环：当flag为true时，表示已经点击了预订按钮了，就不用再查询了
                        break
                    else:
                        time.sleep(self.refresh_tm)
                        continue
                    # time.sleep(2)
                except Exception as e:
                    print(e, datetime.now())

        else:          # 指定具体车次则走else这条路
            count = 0
            while self.driver.current_url == self.queryUrl:             # 当前页面不是查询页面时说明预定成功了，跳出循环
                self.driver.find_element_by_id("query_ticket").click()  # 点击查询按钮，余票查询
                count += 1
                print("点击查询按钮{}次".format(count), datetime.now())
                try:
                    # 判断指定车次的指定席位是否有剩余，若有剩余则点击预订按钮，若所有指定车次指定席位都无剩余则重新点击查询按钮
                    for train in self.trainNumber:                              # 遍历指定的所有车次
                        if self.seatClass == []:                                # 如果没有指定具体席别，则直接点击预订按钮
                            if self.isbookable(train):                          # 判断车次是否可预订
                                self.getElemFromTrain(train, 13).click()        # 定位并点击预订按钮
                                flag = True
                                # time.sleep(1)
                                break
                            else:
                                continue
                        else:                                                   # 若指定了席别则走else这条路
                            for seat in self.seatClass:                         # 遍历某车次的所有指定席位
                                if self.has_tickets(train, seat):               # 判断：如果该车次的指定席别有票
                                    self.getElemFromTrain(train, 13).click()    # 定位并点击预订按钮
                                    # time.sleep(1)
                                    flag = True
                                    break
                                else:
                                    continue
                            if flag:                # 判断：如果订票成功(即点击预订按钮成功), 退出外层的for循环
                                break
                            else:                   # 否则，迭代指定的下一个车次
                                continue

                    if flag:        # 控制最外层的while循环：当flag为true时，表示已经点击了预订按钮了，就不用再查询了
                        break
                    else:
                        time.sleep(self.refresh_tm)
                        continue
                    # time.sleep(2)
                except Exception as e:
                    print(e, datetime.now())

    def bookTickets(self):
        """
            订票：控制整个流程，包括访问、添加cookies、查票、订票、选择乘客、选择席别、提交订单。
        """
        sucs_for_choose_seatclass = False       # 选择是否成功，座位flag标记，控制是否循环，为False循环，为True时跳出循环

        # 此while循环主要是为了控制：当在乘客选择页面选择席别时，发现没有指定席别了，需要返回余票查询页面重新查询和预订
        while not sucs_for_choose_seatclass:
            self.addCookies()               # 进入余票查询页面，组装车票查询的必要cookies

            # # 当显示余票查询页面时，查询及预订操作
            # while self.driver.current_url != self.queryUrl:
            #     time.sleep(1)
            time.sleep(1)
            self.queryAndReserve()          # 查询及预订

            # 当显示选择乘客页面时，选择乘客和席别
            while self.driver.current_url != self.choosePassengersUrl:
                time.sleep(1)
            # time.sleep(1)
            self.choosePassengers()                                 # 选择乘客
            sucs_for_choose_seatclass = self.chooseSeatClass()      # 选择席别
            logging.info("选择席别是否成功：{}".format(sucs_for_choose_seatclass))

            # 通过选择席别返回的值判断是否需要返回余票查询页面重新查询及预订（为False需返回重新订票，为True时可提交订单）
            if sucs_for_choose_seatclass:
                self.submitOrder()          # 提交订单
                print("\n**********订票成功**********", datetime.now())
                break
            else:
                print("选择席别失败，返回余票查询页面重新查询和预订！", datetime.now())
                continue

        print("请在30分钟内完成付款，谢谢使用！\nEnd!", datetime.now())


def main():
    """
        主函数
    """
    usrName = "请输入自己的12306的登录名"             # 定义登录名
    startStation = "南充"                            # 出发地
    endStation = "安康"                              # 目的地
    dtime = "2019-02-16"                             # 日期
    trainNumber = ['K4638']                          # 车次（空列表[]代表所有车次，即不指定特定车次），把有余票的车次和席别写在列表中靠前位置执行效率会高许多
    passengers = ['乘客1', "乘客2"]                  # 乘客列表（必须为12306登录账号中已包含的乘客）
    seatClass = ['硬座']                             # 席别列表（空列表[]代表任意席别，即不指定特定席别），把有余票的车次和席别写在列表中靠前位置执行效率会高许多

    password = input("请输入12306账号的登录密码：")

    # 登录
    bookTicketObj = BookTickets(usrName, password, startStation, endStation, dtime, trainNumber, passengers, seatClass)
    bookTicketObj.login()

    # 订票
    bookTicketObj.bookTickets()


if __name__ == "__main__":
    main()