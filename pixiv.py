import bs4
import json
import requests
from fake_useragent import UserAgent


class Pixiv(object):
	login_post_url = "https://accounts.pixiv.net/api/login?lang=zh"
	login_data_url = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
	rank_today_url = "https://www.pixiv.net/ranking.php?mode={mode}&p={count}&format=json"
	rank_date_url = "https://www.pixiv.net/ranking.php?mode={mode}&p={count}&date={date}&format=json"
	headers = {"user-agent": UserAgent().random}

	def __init__(self, account, password, download_count=100):
		self.session = requests.session()
		self.download_count = download_count
		self._login(account, password)

	def _login(self, account, password):
		print("正在登陆")
		data = self.session.get(url=self.login_data_url, headers=self.headers, verify=False).content.decode("utf8")
		post_key = bs4.BeautifulSoup(data, "lxml").find(attrs={"name": "post_key"})["value"]
		login_data = {
			"pixiv_id": account,
			"password": password,
			"post_key": post_key,
			"source": "pc",
			"ref": "wwwtop_accounts_index",
			"return_to": "https://www.pixiv.net/",
		}
		self.session.post(url=self.login_post_url, data=login_data)
		cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
		cookie = ""
		for k, v in cookies.items():
			cookie += k + "=" + v + "; "
		self.headers["cookie"] = cookie[:-2]
		print("登陆完毕")

	def get_headers(self):
		return self.headers.copy()

	def get_rank_list(self, date=None, r18=False):
		"""
		:param date: like 20200101
		:param r18: is r18 rank
		:return:
		"""

		count = 1
		pid_list = []
		mode = "daily" if not r18 else "daily_r18"
		for page in range(1, self.download_count + 1, 50):
			if date:
				rank_url = self.rank_date_url.format(mode=mode, count=count, date=date)
			else:
				rank_url = self.rank_today_url.format(mode=mode, count=count)
			print("正在拉取", date, "的排行榜数据:", rank_url)

			try:
				text = self.session.get(rank_url).text
				json_data = json.loads(text)
			except Exception as e:
				print("拉取数据失败", e.args)
				return []

			if "error" in json_data:
				print(json_data)
				return []

			for item in json_data["contents"]:
				if item["rank"] < page + min(self.download_count, 50) and len(pid_list) < self.download_count:
					pid_list.append(item["illust_id"])
			count += 1
		print("排行榜数据拉取完成")
		return pid_list
