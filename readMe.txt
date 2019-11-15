1. 全套包括：余票查询、订票
2. 余票查询使用方法：在终端进入该套程序所在文件夹，输入python Query_Tickets.py a 出发地如北京 目的地西安 时间如2019-01-01
3. 订票使用方法：在终端进入该套程序所在文件夹，输入python booking_tickets.py
4. 注意事项：
  4.1 余票查询： 
Query_Tickets.py中用到了一个余票查询的url，12306会经常对该url进行变更，所以当读者您拿到这个脚本时，可能12306的余票查询url已经变更了，那么您就需要自己在Query_Tickets.py文件——Query_Ticket类——query方法中修改self.url变量，修改方法：如下，仅需要把第1行的‘Z’改成其他字符或删除（具体该改成什么，可以通过浏览器进行查票，在查票时抓包，获取当前正确的查询url）
self.url = ("https://kyfw.12306.cn/otn/leftTicket/queryZ?"
			   "leftTicketDTO.train_date={}&"
			   "leftTicketDTO.from_station={}&"
			   "leftTicketDTO.to_station={}&"
			   "purpose_codes=ADULT").format(self.date, self.from_station, self.to_station)
  4.2 订票：
booking_tickets.py中，在文件开始处附近，定义了一个城市cookies变量，如下。如果在订票时，你要选择的出发站和目的站没有在这个字典中，就需要您自己在该字典中添加城市的cookies，城市的cookies可以通过chrome浏览器在查询余票的同时抓包获取。
CityCookies = {"北京": "%u5317%u4EAC%2CBJP", "上海": "%u4E0A%u6D77%2CSHH", "天津": "%u5929%u6D25%2CTJP", "西安": "%u897F%u5B89%2CXAY",
               "重庆": "%u91CD%u5E86%2CCQW", "长沙": "%u957F%u6C99%2CCSQ", "长春": "%u957F%u6625%2CCCT", "成都": "%u6210%u90FD%2CCDW",
               "深圳": "%u6DF1%u5733%2CSZQ", "杭州": "%u676D%u5DDE%2CHZH", "广州": "%u5E7F%u5DDE%2CGZQ", "福州": "%u798F%u5DDE%2CFZS",
               "南京": "%u5357%u4EAC%2CNJH", "石家庄": "%u77F3%u5BB6%u5E84%2CSJP", "合肥": "%u5408%u80A5%2CHFH",
               "昆明": "%u6606%u660E%2CKMM", "银川": "%u94F6%u5DDD%2CYIJ", "武汉": "%u6B66%u6C49%2CWHN", "西宁": "%u897F%u5B81%2CXNO",
               "厦门": "%u897F%u5B81%2CXNO"}

5. 环境搭建：python3.7、selenium3.141、FireFox64、Chrome71、Geckodriver0.23.0（geckodriver需要放到环境变量中如/usr/local/bin）。



