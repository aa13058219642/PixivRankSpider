import os
import json
import time
import queue
import requests
from threading import Thread
from fake_useragent import UserAgent
from GIFDownloader import GIFDownloader


class Downloader(object):
	referer_template = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id={pid}"
	img_info_url = "https://www.pixiv.net/ajax/illust/{pid}"

	headers = {"user-agent": UserAgent().random}

	def __init__(self, save_path, pixiv_header, max_threads=8):
		self.save_path = save_path
		self.max_threads = max_threads

		self.th_pool = []
		self.data_queue = queue.Queue()
		self.gif_downloader = GIFDownloader(pixiv_header, save_path)

		self.count = 0
		self.failure = 0
		self.data_size = -1

	def download(self, pid_list, block=True):
		self.data_size = len(pid_list)
		if self.data_size == 0:
			return

		for pid in pid_list:
			self.data_queue.put(pid)

		for i in range(self.max_threads):
			i = Thread(target=self.download_thread)
			self.th_pool.append(i)
			i.start()

		if block:
			while not self.data_queue.empty():
				time.sleep(0.1)
			for th in self.th_pool:
				th.join()
			self.th_pool.clear()

	def download_thread(self):
		while True:
			if self.data_queue.empty():
				break
			pid = self.data_queue.get()
			self._download(pid)

	def _download(self, pid):
		dir_path = os.path.join(self.save_path, str(pid))
		if not os.path.exists(dir_path):
			os.makedirs(dir_path)

		if self.gif_downloader.isGIF(pid):
			self.gif_downloader.download(pid)
		else:
			headers = self.headers.copy()
			info_url = self.img_info_url.format(pid=pid)
			res = requests.get(info_url, headers=headers)
			js = json.loads(res.text)
			img_url = js["body"]["urls"]["original"]
			replace_template = "_p{page}"

			count = -1
			while True:
				img_url = img_url.replace(replace_template.format(page=count), replace_template.format(page=count + 1))
				print("download from", img_url)
				res = requests.get(img_url, headers=headers, verify=False)
				count += 1
				if res.status_code != 200:
					break
				with open(str(count) + ".jpg", "wb+") as fp:
					fp.write(res.content)

			count = -1
			while True:
				headers["referer"] = self.referer_template.format(pid=pid)
				img_url = img_url.replace(replace_template.format(page=count), replace_template.format(page=count + 1))
				print("download from", img_url)
				img_res = requests.get(img_url, headers=headers, verify=False)
				if img_res.status_code != 200:
					break
				image_format = img_url.split(".")[-1]
				file_name = "{pid}_p{page}.{format}".format(pid=pid, page=count + 1, format=image_format)
				file_name = os.path.join(dir_path, file_name)
				with open(file_name, "wb+") as fp:
					fp.write(img_res.content)

				count += 1
		self.count += 1
		print(pid, "下载完成。当前进度：", self.count, "/", self.data_size, )
