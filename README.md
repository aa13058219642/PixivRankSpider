

# Pixiv Rank Spider
P站每日排行榜爬虫

# requirements
```
    pip install bs4
    pip install lxml
    pip install imageio
    pip install fake_useragent
```

# usage
```
    python main.py -m today				# 下载今日排行榜
    python main.py -m date -d 20200101			# 下载2020-01-01的排行榜
    python main.py -m d2t -d 20200101			# 下载2020-01-01到今天的每日排行榜
    python main.py -m d2d -d 20200101 -d2 20200131	# 下载2020年1月份的每日排行榜
```

更多选项参见`python main.py -h`或`config.json`