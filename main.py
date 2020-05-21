import os
import sys
import json
import datetime
import argparse

from downloader import Downloader
from pixiv import Pixiv


def load_config():
	fp = open("config.json", "r", encoding='utf-8')
	js = json.load(fp)
	fp.close()
	assert isinstance(js, dict)
	return js


def formal_date(number):
	try:
		if number == 0:
			date = datetime.date.today()
		else:
			y = int(number / 10000)
			m = int((number - y * 10000) / 100)
			d = int(number % 100)
			date = datetime.date(y, m, d)
	except ValueError:
		return None

	return date


if __name__ == "__main__":
	config = load_config()
	max_threads = config.get("max_threads", 8)

	epilog = "example:\n"
	epilog += "python main.py -m today					# 下载今日排行榜\n"
	epilog += "python main.py -m date -d 20200101		# 下载2020-01-01的排行榜\n"
	epilog += "python main.py -m d2t -d 20200101		# 下载2020-01-01到今天的每日排行榜\n"
	epilog += "python main.py -m d2d -d 20200101 -d2 20200131		# 下载2020年1月份的每日排行榜\n"

	parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("-m", "--mode", choices=["today", "date", "d2t", "d2d"], default="today", help="mode")
	parser.add_argument("-s", "--save-path", default=config.get("save_path", "Download"))
	parser.add_argument("-d", "--date", type=int, default=0, help="like 20200101")
	parser.add_argument("-d2", "--date2", type=int, default=0, help="like 20200101")
	parser.add_argument("-a", "--account", type=str, default=config.get("account", ""))
	parser.add_argument("-p", "--password", type=str, default=config.get("password", ""))
	parser.add_argument("-c", "--count", type=int, default=config.get("download_count", 2))
	parser.add_argument("-r18", action="store_true", default=False)

	args = parser.parse_args()

	if args.account == "" or args.password == "":
		print("需要登陆，请添加参数：-a 账号 -p 密码")
		sys.exit(0)
	pixiv = Pixiv(args.account, args.password, args.count)

	if args.r18:
		save_path = os.path.join(args.save_path, "r18")
	else:
		save_path = os.path.join(args.save_path, "normal")

	if args.mode == "today":
		today = datetime.date.today()
		date = "%04d%02d%02d" % (today.year, today.month, today.day)
		pid_list = pixiv.get_rank_list(r18=args.r18)

		path = os.path.join(save_path, date)
		downloader = Downloader(path, pixiv.get_headers(), max_threads)
		downloader.download(pid_list, block=True)

	else:
		date = formal_date(args.date)
		if not date:
			print("日期格式有误")
			sys.exit(0)

		if args.mode == "date":
			d = "%04d%02d%02d" % (date.year, date.month, date.day)
			pid_list = pixiv.get_rank_list(d, r18=args.r18)

			path = os.path.join(save_path, str(d))
			downloader = Downloader(path, pixiv.get_headers(), max_threads)
			downloader.download(pid_list, block=True)
		elif args.mode == "d2t":
			today = datetime.date.today()
			while (today - date).days >= 0:
				d = date.year * 10000 + date.month * 100 + date.day
				pid_list = pixiv.get_rank_list(d, r18=args.r18)

				path = os.path.join(save_path, str(d))
				downloader = Downloader(path, pixiv.get_headers(), max_threads)
				downloader.download(pid_list, block=True)

				date += datetime.timedelta(days=1)

		elif args.mode == "d2d":
			date2 = formal_date(args.date2)
			if not date2:
				print("日期格式有误")
				sys.exit(0)

			while (date2 - date).days >= 0:
				d = date.year * 10000 + date.month * 100 + date.day
				pid_list = pixiv.get_rank_list(d, r18=args.r18)

				path = os.path.join(save_path, str(d))
				downloader = Downloader(path, pixiv.get_headers(), max_threads)
				downloader.download(pid_list, block=True)

				date += datetime.timedelta(days=1)

	print("done")
