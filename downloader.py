import os
import json
import time
import queue
import requests
from threading import Thread
from fake_useragent import UserAgent
from GIFDownloader import GIFDownloader


class Downloader(object):
	referer_url = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id={pid}"
	img_info_url = "https://www.pixiv.net/ajax/illust/{pid}"

	def __init__(self, save_path, pixiv_header, max_threads=8, timeout=180, max_retry=5, new_dir=False):
		self.save_path = save_path
		self.max_threads = max_threads
		self.timeout = timeout
		self.max_retry = max_retry
		self.new_dir = new_dir

		self.th_pool = []
		self.data_queue = queue.Queue()
		self.gif_downloader = GIFDownloader(pixiv_header, save_path)

		self._complete = queue.Queue()
		self._failure = queue.Queue()
		self.complete = []
		self.failure = []
		self.data_size = -1

	def write_log(self, msg):
		log_file = os.path.join(self.save_path, "_error.log")
		fp = open(log_file, "a")
		fp.write(msg + "\n")
		fp.close()

	def download(self, rank_list, block=True):
		self.data_size = len(rank_list)
		if self.data_size == 0:
			return

		for item in rank_list:
			pid = item["illust_id"]
			self.data_queue.put((pid, 0))

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

		while not self._failure.empty():
			pid = self._failure.get()
			self.write_log("download fail: %d" % pid)
			self.failure.append(pid)

		while not self._complete.empty():
			pid = self._complete.get()
			self.complete.append(pid)

	def download_thread(self):
		while True:
			if self.data_queue.empty():
				break
			pid, retry = self.data_queue.get()
			self._work(pid, retry)

	def _work(self, pid, retry):
		if self.new_dir:
			dir_path = os.path.join(self.save_path, str(pid))
			if not os.path.exists(dir_path):
				os.makedirs(dir_path)
		else:
			dir_path = self.save_path

		if self.gif_downloader.isGIF(pid):
			self.gif_downloader.download(pid)
		else:
			headers = {"user-agent": UserAgent().random}
			info_url = self.img_info_url.format(pid=pid)

			try:
				res = requests.get(info_url, headers=headers, timeout=self.timeout)
				js = json.loads(res.text)
				img_url = js["body"]["urls"]["original"]
			except Exception:
				if retry < self.max_retry:
					self.data_queue.put((pid, retry + 1))
				else:
					print("下载%d失败" % pid)
					self._failure.put(pid)
				return

			replace_template = "_p{page}"

			page = -1
			while True:
				headers["referer"] = self.referer_url.format(pid=pid)
				img_url = img_url.replace(replace_template.format(page=page), replace_template.format(page=page + 1))
				print("download from", img_url)

				try:
					img_res = requests.get(img_url, headers=headers, timeout=self.timeout)
					if img_res.status_code != 200:
						break
				except Exception:
					if retry < self.max_retry:
						self.data_queue.put((pid, retry + 1))
					else:
						print("下载%d失败" % pid)
						self._failure.put(pid)
					return

				image_format = img_url.split(".")[-1]
				file_name = "{pid}_p{page}.{format}".format(pid=pid, page=page + 1, format=image_format)
				file_name = os.path.join(dir_path, file_name)
				with open(file_name, "wb+") as fp:
					fp.write(img_res.content)

				page += 1
		self._complete.put(pid)
		print(pid, "下载完成。当前进度：", len(self._complete), "/", self.data_size)
