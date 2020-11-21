import bs4
import json
import requests
import traceback
from fake_useragent import UserAgent


class Pixiv(object):
    login_post_url = "https://accounts.pixiv.net/api/login?lang=zh"
    login_data_url = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
    rank_url = "https://www.pixiv.net/ranking.php?format=json&content=illust"

    def __init__(self, account, password):
        self.headers = {"user-agent": UserAgent().random}
        self.session = requests.session()
        self.initialized = False
        self._login(account, password)
        self.unique = False
        self.pid_set = None

    def use_pid_set(self, unique, pid_set=None):
        self.unique = unique
        self.pid_set = pid_set

    def _login(self, account, password):
        print("正在登陆")
        try:
            data = self.session.get(url=self.login_data_url, headers=self.headers, timeout=60).content.decode("utf8")
            post_key = bs4.BeautifulSoup(data, "lxml").find(attrs={"name": "post_key"})["value"]
            login_data = {
                "pixiv_id": account,
                "password": password,
                "post_key": post_key,
                "source": "pc",
                "ref": "wwwtop_accounts_index",
                "return_to": "https://www.pixiv.net/",
            }
            self.session.post(url=self.login_post_url, headers=self.headers, data=login_data)
            cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
            cookie = ""
            for k, v in cookies.items():
                cookie += k + "=" + v + "; "
            self.headers["cookie"] = cookie[:-2]
        except Exception as e:
            traceback.print_stack()
            return False

        self.initialized = True
        print("登陆完毕")
        return True

    def get_headers(self):
        return self.headers.copy()

    def _filter_data(self, illust_list, filter_func=None):
        target = []
        for item in illust_list:
            if filter_func:
                if filter_func(item):
                    target.append(item)
            else:
                target.append(item)
        return target

    def _get_rank(self, rank_url, count, filter_func=None):
        rank_list = []
        page = 1
        print("拉取数据:", rank_url)
        while len(rank_list) < count:
            url = rank_url + "&p=" + str(page)
            try:
                text = self.session.get(url, headers=self.headers, timeout=60).text
                illust_list = json.loads(text)
            except json.JSONDecodeError as e:
                print("拉取数据失败，网页账号可能被ban了：\n", e.args, url)
                return False, []
            except Exception as e:
                print("拉取数据失败:", e.args, url)
                return False, []

            if "error" in illust_list:
                print("拉取数据失败:", illust_list, url)
                return True, []

            target = self._filter_data(illust_list["contents"], filter_func)
            if self.unique:
                target = [item for item in target if item["illust_id"] not in self.pid_set]
            rank_list.extend(target)

            if illust_list["next"]:
                page += 1
            else:
                break

        rank_list = rank_list[:count]
        print("找到符合条件的图片 %d 张" % len(rank_list))
        return True, rank_list

    def get_today_rank(self, top=100, r18=False, filter_func=None):
        """
        :param top: top rank
        :param r18: is r18 rank
        :param filter_func: filter function
        :return: list
        """

        mode = "daily" if not r18 else "daily_r18"
        count = top if top <= 500 else 500
        rank_url = self.rank_url + "&mode=" + mode
        return self._get_rank(rank_url, count, filter_func)

    def get_date_rank(self, date, top=100, r18=False, filter_func=None):
        """
        :param date: like 20200101
        :param top: top rank
        :param r18: is r18 rank
        :param filter_func: filter function
        :return: list
        """

        mode = "daily" if not r18 else "daily_r18"
        count = top if top <= 500 else 500
        rank_url = self.rank_url + "&mode=%s&date=%d" % (mode, date)
        return self._get_rank(rank_url, count, filter_func)
