import os
import sys
import json
import imageio
import argparse
from Script.spider import PixivRankSpider


def load_config():
    fp = open("config.json", "r", encoding='utf-8')
    js = json.load(fp)
    fp.close()
    assert isinstance(js, dict)
    return js


if __name__ == "__main__":
    config = load_config()

    epilog = "example:\n"
    epilog += "python main.py -m today                    # 下载今日排行榜\n"
    epilog += "python main.py -m date -d 20200101        # 下载2020-01-01的排行榜\n"
    epilog += "python main.py -m d2t -d 20200101        # 下载2020-01-01到今天的每日排行榜\n"
    epilog += "python main.py -m d2d -d 20200101 -d2 20200131        # 下载2020年1月份的每日排行榜\n"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-m", "--mode", choices=["today", "yesterday", "date", "d2t", "d2d"], default="today")
    parser.add_argument("-s", "--save-path", default=config.get("save_path", "Download"))
    parser.add_argument("-d", "--date", type=int, default=0, help="like 20200101")
    parser.add_argument("-d2", "--date2", type=int, default=0, help="like 20200101")
    parser.add_argument("--cookie", type=str, default=config.get("cookie", ""))
    parser.add_argument("--account", type=str, default=config.get("account", ""))
    parser.add_argument("--password", type=str, default=config.get("password", ""))
    parser.add_argument("-c", "--count", type=int, default=config.get("download_count", 2))
    parser.add_argument("-r18", action="store_true", default=config.get("r18", False))
    parser.add_argument("-unique", action="store_true", default=config.get("unique", False))
    parser.add_argument("-dig", action="store_true", default=config.get("dig", False))

    args = parser.parse_args()
    if args.account == "" or args.password == "":
        print("需要登陆，请添加参数：-a 账号 -p 密码")
        sys.exit(0)

    spider = PixivRankSpider(config, args)
    if not spider.initialized:
        os.system("pause")
        sys.exit(-1)

    # # use filter
    # def filter_func(illust_data):
    #     """
    #     注意:
    #         如果pid是合集，width 和 height 只对合集的第一张图有用
    #     """
    #
    #     pid = illust_data["illust_id"]
    #     if illust_data['width'] < 1920 or illust_data['height'] < 1080:
    #         return False
    #     if illust_data['width'] < illust_data['height']:
    #         return False
    #     return True
    #
    # def download_callback(file_path):
    #     try:
    #         img = imageio.imread(file_path)
    #         h = img.shape[0]
    #         w = img.shape[1]
    #     except Exception:
    #         os.remove(file_path)
    #
    #     if w < 1920 or h < 1080 or w < h:
    #         os.remove(file_path)
    #
    # spider.set_filter(filter_func)
    # spider.set_downloaded_callback(download_callback)

    if not spider.run():
        os.system("pause")
    else:
        print("done")
