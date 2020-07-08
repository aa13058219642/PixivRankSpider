import os
import json
import datetime

from .downloader import Downloader
from .pixiv import Pixiv


class PixivRankSpider:
    def __init__(self, config, args):
        self.args = args
        self.config = config
        self.save_path = os.path.join(args.save_path, "R18" if args.r18 else "General")
        self.filter_func = None
        self.downloaded_callback = None

        self.download_config = {
            "max_retry": self.config.get("max_retry", 5),
            "max_threads": self.config.get("max_threads", 8),
            "timeout": self.config.get("download_timeout", 180),
            "new_dir": self.config.get("new_dir_for_per_pid", False)
        }

        self.spider_data = {
            "dig_date": 20180101,
            "pid_list": []
        }

        self.read_spider_date()
        self._pixiv = Pixiv(args.account, args.password)
        if self.args.unique:
            self._pixiv.use_pid_set(True, self.spider_data["pid_list"])

    def set_filter(self, filter_func):
        self.filter_func = filter_func

    def set_downloaded_callback(self, callback_func):
        self.downloaded_callback = callback_func

    def read_spider_date(self):
        if not os.path.exists("spider_data.json"):
            return

        try:
            fp = open("spider_data.json", "r", encoding='utf-8')
            self.spider_data = json.load(fp)
            fp.close()
        except Exception:
            pass

    def write_spider_data(self):
        fp = open("spider_data.json", "w", encoding='utf-8')
        json.dump(self.spider_data, fp, indent=4)
        fp.close()

    def run(self):
        if self.args.mode == "today":
            self.download_today()
            return
        elif self.args.mode == "yesterday":
            self.download(datetime.date.today() - datetime.timedelta(days=1))
            return

        date = self.number2date(self.args.date)
        if not date:
            return

        if self.args.mode == "date":
            self.download(date)

        if self.args.dig:
            dig_date = self.number2date(self.spider_data.get("dig_date", 20180100))
            dig_date += datetime.timedelta(days=1)
            if self.args.mode == "d2t":
                date2 = datetime.date.today()
            elif self.args.mode == "d2d":
                date2 = self.number2date(self.args.date2)
            else:
                date2 = datetime.date.today()

            if not date2 or not dig_date:
                return

            if (dig_date - date).days < 0:
                dig_date = date

            self.dig_date = dig_date
            self.download(dig_date, date2)
        else:
            if self.args.mode == "d2t":
                self.download(date, datetime.date.today())
            elif self.args.mode == "d2d":
                date2 = self.number2date(self.args.date2)
                if not date2:
                    return
                self.download(date, date2)
        pass

    def download_today(self):
        rank_list = self._pixiv.get_today_rank(top=self.args.count, r18=self.args.r18, filter_func=self.filter_func)
        headers = self._pixiv.get_headers()
        date = datetime.date.today()

        path = os.path.join(self.save_path, str(self.date2number(date)))
        self.save_rank_data(path, date, rank_list)
        downloader = Downloader(path, headers, self.download_config, self.downloaded_callback)
        downloader.download(rank_list)

        if self.args.unique:
            self.spider_data["pid_list"].extend(downloader.complete)
            self.write_spider_data()

    def download(self, date1, date2=None):
        date = date1
        date2 = date2 if date2 else date1
        while (date2 - date).days >= 0:
            d = self.date2number(date)
            headers = self._pixiv.get_headers()
            rank_list = self._pixiv.get_date_rank(d, top=self.args.count, r18=self.args.r18, filter_func=self.filter_func)
            if len(rank_list) == 0:
                break

            path = os.path.join(self.save_path, str(d))
            self.save_rank_data(path, date, rank_list)
            downloader = Downloader(path, headers, self.download_config, self.downloaded_callback)
            downloader.download(rank_list)

            if self.args.unique:
                self.spider_data["pid_list"].extend(downloader.complete)
            if self.args.dig:
                self.spider_data["dig_date"] = d
            if self.args.unique or self.args.dig:
                self.write_spider_data()

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
            print("日期格式有误:", number)
            return None

        return date

    def date2number(self, date):
        return date.year * 10000 + date.month * 100 + date.day
