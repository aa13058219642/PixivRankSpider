import os
import json
import datetime

from downloader import Downloader
from pixiv import Pixiv


class PixivRankSpider:
	def __init__(self, config, args):
		self.args = args
		self.config = config
		self.pixiv = Pixiv(args.account, args.password)
		self.save_path = os.path.join(args.save_path, "R18" if args.r18 else "General")
		self.filter_func = None

	def set_filter(self, filter_func):
		self.filter_func = filter_func

	def run(self):
		if self.args.mode == "today":
			self.download_today()
		elif self.args.mode == "yesterday":
			self.download(datetime.date.today() - datetime.timedelta(days=1))
		else:
			date = self.number2date(self.args.date)
			if not date:
				print("日期格式有误")
				return
			if self.args.mode == "date":
				self.download(date)
			elif self.args.mode == "d2t":
				self.download(date, datetime.date.today())
			elif self.args.mode == "d2d":
				date2 = self.number2date(self.args.date2)
				if not date2:
					print("日期格式有误")
					return
				self.download(date, date2)
		pass

	def download_today(self):
		max_retry = self.config.get("max_retry", 5)
		max_threads = self.config.get("max_threads", 8)
		timeout = self.config.get("download_timeout", 180)
		new_dir = self.config.get("new_dir_for_per_pid", False)

		rank_list = self.pixiv.get_today_rank(top=self.args.count, r18=self.args.r18, filter_func=self.filter_func)
		headers = self.pixiv.get_headers()
		date = datetime.date.today()

		path = os.path.join(self.save_path, str(self.date2number(date)))
		self.save_rank_data(path, date, rank_list)
		downloader = Downloader(path, headers, max_threads, timeout, max_retry, new_dir)
		downloader.download(rank_list)

	def download(self, date1, date2=None):
		max_retry = self.config.get("max_retry", 5)
		max_threads = self.config.get("max_threads", 8)
		timeout = self.config.get("download_timeout", 180)
		new_dir = self.config.get("new_dir_for_per_pid", False)

		date = date1
		date2 = date2 if date2 else date1
		while (date2 - date).days >= 0:
			d = self.date2number(date)
			rank_list = self.pixiv.get_date_rank(d, top=self.args.count, r18=self.args.r18, filter_func=self.filter_func)
			headers = self.pixiv.get_headers()

			path = os.path.join(self.save_path, str(d))
			self.save_rank_data(path, date, rank_list)
			downloader = Downloader(path, headers, max_threads, timeout, max_retry, new_dir)
			downloader.download(rank_list)

			date += datetime.timedelta(days=1)

	def save_rank_data(self, save_path, date, rank_list):
		if not os.path.isdir(save_path):
			os.makedirs(save_path)

		file_name = "_rank_%s.json" % str(date)
		file_path = os.path.join(save_path, file_name)
		data = {
			"date": str(date),
			"total": len(rank_list),
			"content": rank_list
		}

		fp = open(file_path, "w", encoding='utf-8')
		json.dump(data, fp, indent=4, ensure_ascii=False)
		fp.close()

	def number2date(self, number):
		try:
			if number == 0:
				date = datetime.date.today()
			else:
				y = int(number / 10000)
				m = int((number - y * 10000) / 100)
				d = int(number % 100)
				date = datetime.date(y, m, d)
		except Exception:
			return None

		return date

	def date2number(self, date):
		return date.year * 10000 + date.month * 100 + date.day