"""
版本：v1.0
查询余票并打印，在购票之前查票用。
Usage:
	Query_Ticket.py [agdtkz] <from> <to> <date>
[gdtkz]:
	a            全部
	d            动车
	g            高铁
	k            快速
	t            特快
	z            直达
<data>:
	year-month-day,需为2018-12-02这样的格式，不能为2018-12-2这样的格式，年为4位、月和日分别都是2位。
"""

import requests
from datetime import datetime, timedelta
from prettytable import PrettyTable
from sys import argv
import logging
import re
import pprint, time

# 日志基础配置
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s-%(levelname)s-%(message)s")
logging.disable(logging.DEBUG)

# 获取参数
ticket_option = argv[1]		# 类型[agdtkz]
from_station = argv[2]		# 出发站
to_station = argv[3]		# 目的站
date = argv[4]				# 日期
dic_station_code = {}		# 站点名称与站点编码之间的对应关系


def get_station_info():
	"""
		:return: 所有站点与站点编码之间的对应关系的字典，如{'北京西':'BXP',...等}
	"""
	global dic_station_code
	try:
		import stations
		dic_station_code = stations.stations
	except:
		logging.info("开始查询特殊Url,获取站点与编码的信息。")
		station_url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9042'  # 特殊的Url，获取站点详细信息url
		res = requests.get(station_url, verify=False)  	# 请求站点详细信息网页，不进行SSL安全校验
		pattern = u'([\u4e00-\u9fa5]+)\|([A-Z]+)'  		# 匹配的模式为：若干汉字|若干字母
		dic_station_code = dict(re.findall(pattern, res.text))  # 站点与编码的字典如{'北京西':'BXP',...}
		with open("stations.py", 'w') as f:
			f.write("stations = " + pprint.pformat(dic_station_code))


def getStationNameFromCode(station_code):
	"""
		根据站点编码查找站点名称
		:station_code: 站点编码，如"BXP"
		:return:站点名称，如"北京西"
	"""
	global dic_station_code
	try:
		return list(dic_station_code.keys())[list(dic_station_code.values()).index(station_code)]
	except:
		return None


def getStationCode(station_name):
	"""
		获取站点编码
		:param station_name: 站点名称，如"北京西"
		:return: 站点编码，如"BXP"
	"""
	global dic_station_code
	try:
		return dic_station_code[station_name]
	except:
		return None


# 数据处理+显示
class Trains_Demo():
	headers = '车次 车站 时间 历时 商务/特等座 一等座 二等座 高级软卧 软卧 动卧 硬卧 软座 硬座 无座'.split()		#生成列表

	# 初始化
	def __init__(self, raw_trains, option):
		"""
			:param raw_trains: 从出发站到目的站的所有车次信息列表，如【<车次1信息>,<车次2信息>...】
			:param option: 类型[agdtkz]，如高铁、动车、所有...
		"""
		self.raw_trains = raw_trains		# 查询到的车次信息列表
		self.option = option		# 票的类型，如高铁票。

	# 获取出发和到达站
	def get_from_to_station_name(self, data_list):
		"""
			:param data_list: 某车次各字段形成的列表
			:return: 出发站和到达站名称，如北京西-->西安北
		"""
		self.from_station_name = data_list[6]		# 获取出发站（编号）
		self.to_station_name = data_list[7]			# 获取到达站（编号）
		# 获取出发站编码、到达站编码对应的站点名称，形成字符串如：北京西-->西安北
		self.from_to_station_name = getStationNameFromCode(self.from_station_name) + '-->' + getStationNameFromCode(self.to_station_name)
		return self.from_to_station_name		# 返回出发站-到达站字符串如：北京西-->西安北

	# 获得出发和到达时间
	def get_start_arrive_time(self, data_list):
		"""
			:param data_list: 某车次各字段形成的列表。
			:return: 出发时间————>到达时间
		"""
		self.start_arrive_time = data_list[8] + '-->' + data_list[9]		# index8为出发时间、index9为到达时间
		return self.start_arrive_time

	# 解析trains数据(与headers依次对应)
	def parse_trains_data(self, data_list):
		"""
			:param data_list: 某车次各字段形成的列表
			:return: 各字段形成的字典
		"""
		return {
			'trips': data_list[3],		# 车次名称
			'from_to_station_name': self.get_from_to_station_name(data_list),		# 如北京西————>西安北
			'start_arrive_time': self.get_start_arrive_time(data_list),		# <出发时间>————><到达时间>
			'duration': data_list[10],			# 历时
			'business_premier_seat': data_list[32] or '--',		# 商务座
			'first_class_seat': data_list[31] or '--',			# 一等座
			'second_class_seat': data_list[30] or '--',			# 二等座
			'senior_soft_sleep': data_list[21] or '--',			# 高级软卧
			'soft_sleep': data_list[23] or '--',				# 软卧
			'move_sleep': data_list[33] or '--',				# 动卧
			'hard_sleep': data_list[28] or '--',				# 硬卧
			'soft_seat': data_list[24] or '--',					# 软座
			'hard_seat': data_list[29] or '--',					# 硬座
			'no_seat': data_list[26] or '--',					# 无座
			# 'others': data_list[34] or '--'					# 其他
			}

	# 判断是否需要显示
	def need_show(self, data_list):
		trips = data_list[3]		# 取得车次名称，如G427
		initial = trips[0].lower()		# 取得车次名称的第1个字母，转成小写
		if self.option == 'a':		# 如果启动命令中包含的车次类型为"a",即所有车次，则返回本记录中的车次，如G427
			return True
		else:						# 否则，如果该车次的首字母在启动命令中指定的车次类型中，则返回true，否则返回false。
			return initial in self.option

	# 数据显示
	def show_trian_data(self):
		self.demo = PrettyTable()
		self.demo._set_field_names(self.headers)		# 表头
		for self.train in self.raw_trains:		# 迭代所有车次记录
			self.data_list = self.train.split('|')		# 取得某车次的各字段数据,形成列表
			if self.need_show(self.data_list):		# 如果经判断，该车次需要显示，则进行后续处理。
				self.values_row = []
				self.parsed_train_data = self.parse_trains_data(self.data_list)		# 获取该车次各字段形成的字典，如{'车次'：.., '出发/到达站':..等}
				self.values_row.append(self.parsed_train_data['trips'])
				self.values_row.append(self.parsed_train_data['from_to_station_name'])
				self.values_row.append(self.parsed_train_data['start_arrive_time'])
				self.values_row.append(self.parsed_train_data['duration'])
				self.values_row.append(self.parsed_train_data['business_premier_seat'])
				self.values_row.append(self.parsed_train_data['first_class_seat'])
				self.values_row.append(self.parsed_train_data['second_class_seat'])
				self.values_row.append(self.parsed_train_data['senior_soft_sleep'])
				self.values_row.append(self.parsed_train_data['soft_sleep'])
				self.values_row.append(self.parsed_train_data['move_sleep'])
				self.values_row.append(self.parsed_train_data['hard_sleep'])
				self.values_row.append(self.parsed_train_data['soft_seat'])
				self.values_row.append(self.parsed_train_data['hard_seat'])
				self.values_row.append(self.parsed_train_data['no_seat'])
				# self.values_row.append(self.parsed_train_data['others'])
				self.demo.add_row(self.values_row)
		print(self.demo)


# 车票查询
class Query_Ticket(object):
	# 初始化
	def __init__(self):
		self.ticket_option = ticket_option					# 类型[agdtkz]
		self.from_station = getStationCode(from_station)  	# 获取出发站的站点编码，如"BXP"
		self.to_station = getStationCode(to_station)  		# 获取目的站的站点编码，如"BXP"
		self.date = date  									# 日期

		# 出发站和目的站校验
		if self.from_station is None or self.to_station is None:
			print('请输入有效车站名...')
			exit()
		# 时间校验
		try:
			delta = timedelta(days=29)		# 29天的时间段
			inputDate = datetime.strptime(self.date, '%Y-%m-%d')		# 把输入的日期字符串转换成datetime格式
			if inputDate.date() < datetime.now().date() or inputDate > (datetime.now() + delta):
				raise ValueError
		except:
			print('请输入有效日期...')
			exit()

	# 查询车票
	def query(self):
		print("正在查询车票，请稍候...")
		# 请求报文头，有些服务器会根据该值判断是否为浏览器发起的请求
		self.headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:63.0) Gecko/20100101 Firefox/63.0'}

		# 查票的url
		self.url = ("https://kyfw.12306.cn/otn/leftTicket/queryZ?"
			   "leftTicketDTO.train_date={}&"
			   "leftTicketDTO.from_station={}&"
			   "leftTicketDTO.to_station={}&"
			   "purpose_codes=ADULT").format(self.date, self.from_station, self.to_station)

		# 查询车票(verify=False代表不进行SSL校验，headers主要是为了满足服务器对请求发起者的检查)
		self.res = requests.get(self.url, headers=self.headers)
		self.res.raise_for_status()
		try:
			time.sleep(0.5)
			self.trains = self.res.json()['data']['result']			# 所有车次信息的列表，如【<车次1信息>,<车次2信息>...】
		except:
			print("车票查询出错，请检查url是否正确。若url确定没错，再多试几遍（有可能是服务器数据还没返回，程序就继续解析了）")
			exit(1)

		logging.info("已查询完成，开始处理查询数据。")
		Trains_Demo(self.trains, self.ticket_option).show_trian_data()		# 数据处理及显示：ticket_option:[agdtkz]


def main():
	"""
		主函数
	"""
	get_station_info()		# 生成站点名称与站点编号之间的全局字典

	# 车票查询
	query_ticket = Query_Ticket()
	query_ticket.query()


if __name__ == '__main__':
	main()
