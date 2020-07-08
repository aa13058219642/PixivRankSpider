import os
import json
import time
import queue
import requests
from threading import Thread
from fake_useragent import UserAgent
from .GIFDownloader import GIFDownloader


class Downloader(object):
    referer_url = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id={pid}"
    img_info_url = "https://www.pixiv.net/ajax/illust/{pid}"

    def __init__(self, save_path, pixiv_header, config=None, downloaded_callback=None):
        self.th_pool = []
        self.url_queue = queue.Queue()
        self.pid_queue = queue.Queue()
        self._complete = queue.Queue()
        self._failure = queue.Queue()
        self.complete = []
        self.failure = []
        self.data_size = 0
        self.max_threads = 8
        self.timeout = 180
        self.max_retry = 5
        self.new_dir = False

        self.save_path = save_path
        self.downloaded_callback = downloaded_callback

        if config:
            self.set_config(config)

        self.gif_downloader = GIFDownloader(pixiv_header, save_path)

    def set_config(self, config):
        self.max_threads = config["max_threads"] if "max_threads" in config else self.max_threads
        self.timeout = config["timeout"] if "timeout" in config else self.timeout
        self.max_retry = config["max_retry"] if "max_retry" in config else self.max_retry
        self.new_dir = config["new_dir"] if "new_dir" in config else self.new_dir

    def _write_log(self, msg):
        log_file = os.path.join(self.save_path, "_error.log")
        fp = open(log_file, "a")
        fp.write(msg + "\n")
        fp.close()

    def download(self, rank_list, block=True):
        if len(rank_list) == 0:
            return

        self._download_illust_info(rank_list)

        self.data_size = self.url_queue.qsize()
        print("获取对应合集，共 %d 张" % self.data_size)
        if self.data_size == 0:
            return

        self._download_image(block)

    def _download_illust_info(self, rank_list):
        for item in rank_list:
            pid = item["illust_id"]
            self.pid_queue.put((pid, 0))

        for i in range(self.max_threads):
            i = Thread(target=self._work_thread, args=(self._info_worker, self.pid_queue))
            self.th_pool.append(i)
            i.start()

        while not self.pid_queue.empty():
            time.sleep(0.1)

        for th in self.th_pool:
            th.join()
        self.th_pool.clear()

    def _download_image(self, block):
        if self.url_queue.empty():
            return

        for i in range(self.max_threads):
            i = Thread(target=self._work_thread, args=(self._illust_worker, self.url_queue))
            self.th_pool.append(i)
            i.start()

        if block:
            while not self.url_queue.empty():
                time.sleep(0.1)
            for th in self.th_pool:
                th.join()
            self.th_pool.clear()

        pid_set = set()
        while not self._failure.empty():
            pid = self._failure.get()
            self._write_log("download fail: %d" % pid)
            pid_set.add(pid)
        self.failure = list(pid_set)

        pid_set.clear()
        while not self._complete.empty():
            pid = self._complete.get()
            assert isinstance(pid, int)
            pid_set.add(pid)
        self.complete = list(pid_set)

    def _work_thread(self, work_func, queue):
        while True:
            if queue.empty():
                break
            work_func(queue.get())

    def _info_worker(self, queue_data):
        pid, retry = queue_data

        headers = {"user-agent": UserAgent().random}
        info_url = self.img_info_url.format(pid=pid)

        try:
            res = requests.get(info_url, headers=headers, timeout=5)
            js = json.loads(res.text)
        except Exception:
            if retry < self.max_retry:
                self.pid_queue.put((pid, retry + 1))
            return

        urls = []
        count = js["body"]["pageCount"]
        for i in range(count):
            img_url = js["body"]["urls"]["original"]
            img_url = img_url.replace("_p0", "_p%d" % i)

            self.url_queue.put((img_url, 0))
            urls.append(img_url)

    def _illust_worker(self, queue_data):
        url, retry = queue_data
        file_name = os.path.basename(url)
        pid = file_name.split("_")[0]
        print("download", file_name, "from", url)

        if self.new_dir:
            dir_path = os.path.join(self.save_path, str(url))
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        else:
            dir_path = self.save_path

        headers = {"user-agent": UserAgent().random}
        headers["referer"] = self.referer_url.format(pid=pid)
        try:
            img_res = requests.get(url, headers=headers, timeout=self.timeout)
            if img_res.status_code != 200:
                raise Exception()
        except Exception:
            self.retry(url, retry)
            return

        file_name = os.path.basename(url)
        file_path = os.path.join(dir_path, file_name)
        try:
            with open(file_path, "wb+") as fp:
                fp.write(img_res.content)

            if self.downloaded_callback:
                self.downloaded_callback(file_path)
        except Exception:
            self.retry(url, retry)
            return

        self._complete.put(int(pid))
        print(file_name, "complete", "(%d/%d)" % (self._complete.qsize(), self.data_size))

    def retry(self, url, count):
        if count < self.max_retry:
            self.url_queue.put((url, count + 1))
        else:
            print("下载%d失败" % url)
            self._failure.put(url)
        return
