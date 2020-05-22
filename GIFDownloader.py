import os
import json
import zipfile
import imageio
import requests
from fake_useragent import UserAgent


class GIFDownloader(object):
	login_post_url = "https://accounts.pixiv.net/api/login?lang=zh"
	login_data_url = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
	gif_info_url = "https://www.pixiv.net/ajax/illust/{pid}/ugoira_meta"
	referer_url = "https://www.pixiv.net/me"

	def __init__(self, http_headers, save_path, new_dir=False, log=False):
		self.headers = http_headers
		self.save_path = save_path
		self.new_dir = new_dir
		self.log_flag = log

	def log(self, *log_info):
		if self.log_flag:
			str_log = ""
			for info in log_info:
				str_log += str(info)
			print(str_log)

	def show(self):
		while True:
			data = input("输入GIF PID或URL：")
			if not data.isdigit() and not data.startswith("http"):
				print("输入有误，请重新输入。")
				continue
			if data.isdigit():
				pid = int(data)
			else:
				data = data.strip("/")
				pid = data.split("=")[-1]
				if not pid.isdigit():
					print("输入有误，请重新输入。")
					continue
			self.download(pid)
			print(pid, "下载成功")

	def isGIF(self, pid):
		headers = self.headers.copy()
		headers["referer"] = self.referer_url.format(pid=pid)
		gif_info = json.loads(requests.get(self.gif_info_url.format(pid=pid), headers=headers).text)
		return not gif_info["error"]

	def download(self, pid):
		headers = self.headers.copy()
		headers["referer"] = self.referer_url.format(pid=pid)
		file_path = os.path.join(self.save_path, str(pid))
		if not os.path.exists(file_path):
			os.mkdir(file_path)

		# 获取gif信息，提取zip url
		gif_info = json.loads(requests.get(self.gif_info_url.format(pid=pid), headers=headers).text)
		delay = [item["delay"] for item in gif_info["body"]["frames"]]
		delay = sum(delay) / len(delay)
		zip_url = gif_info["body"]["originalSrc"]

		# 下载压缩包
		self.log("开始下载")
		gif_data = requests.get(zip_url, headers=headers)
		gif_data = gif_data.content
		zip_path = os.path.join(file_path, "temp.zip")
		with open(zip_path, "wb+") as fp:
			fp.write(gif_data)

		# 生成文件
		self.log("生成临时文件")
		temp_file_list = []
		zipo = zipfile.ZipFile(zip_path, "r")
		for file in zipo.namelist():
			temp_file_list.append(os.path.join(file_path, file))
			zipo.extract(file, file_path)
		zipo.close()

		# 读取所有静态图片，合成gif
		self.log("生成GIF")
		image_data = []
		for file in temp_file_list:
			image_data.append(imageio.imread(file))
		if self.new_dir:
			path = os.path.join(file_path, str(pid) + ".gif")
		else:
			path = os.path.join(self.save_path, str(pid) + ".gif")
		imageio.mimsave(path, image_data, "GIF", duration=delay / 1000)

		# 清除所有中间文件。
		self.log("清除临时文件")
		for file in temp_file_list:
			os.remove(file)
		os.remove(zip_path)
		if not self.new_dir:
			os.removedirs(file_path)
		self.log(pid, "下载完成")
