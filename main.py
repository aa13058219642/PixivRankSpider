import sys
import json
import argparse

from spider import PixivRankSpider


def load_config():
	fp = open("config.json", "r", encoding='utf-8')
	js = json.load(fp)
	fp.close()
	assert isinstance(js, dict)
	return js


if __name__ == "__main__":
	config = load_config()
	max_retry = config.get("max_retry", 5)
	max_threads = config.get("max_threads", 8)
	timeout = config.get("download_timeout", 180)
	new_dir = config.get("new_dir_for_per_pid", False)

	epilog = "example:\n"
	epilog += "python main.py -m today					# 下载今日排行榜\n"
	epilog += "python main.py -m date -d 20200101		# 下载2020-01-01的排行榜\n"
	epilog += "python main.py -m d2t -d 20200101		# 下载2020-01-01到今天的每日排行榜\n"
	epilog += "python main.py -m d2d -d 20200101 -d2 20200131		# 下载2020年1月份的每日排行榜\n"

	parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("-m", "--mode", choices=["today", "yesterday", "date", "d2t", "d2d"], default="today", help="mode")
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

	spider = PixivRankSpider(config, args)
	spider.run()

	# # use filter
	# def filter_func(illust_data):
	# 	"""
	# 	注意:
	# 	1. width和height只对合集的第一张图有用
	# 	"""
	#
	# 	pid = illust_data["illust_id"]
	# 	if '風景' in illust_data['tags']:
	# 		return False
	# 	return True
	#
	# spider = PixivRankSpider(config, args)
	# spider.set_filter(filter_func)
	# spider.run()

	print("done")
