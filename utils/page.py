"""https://www.xiaohongshu.com/explore"""
"""https://www.bilibili.com/"""
"""https://www.zhihu.com/answer/"""


import jieba
from abc import ABC, abstractmethod
from itertools import chain


class Page(ABC):
    
    def __init__(self, page_item) -> None:
        super().__init__()
        self.user_name = None
        self.user_id = None
        self.ptype = None
        self.title = None
        self.excerpt = None
        self.access_url = None
        self.web_id = None
        self.tokens = None
        self.parse(page_item)

    @abstractmethod
    def parse(self, page_item: dict):
        pass

    # def add_token(self, tokens)

class BiliPage(Page):
    AccessBase = "https://www.bilibili.com/video/"

    def __init__(self, page_item) -> None:
        super().__init__(page_item)

    def parse(self, page_item: dict):
        self.web_id = str(page_item["bvid"])
        self.access_url = self.AccessBase + self.web_id
        self.title = page_item["title"]
        self.ptype = "video"
        self.user_name = page_item["owner"]["name"]
        self.user_id = page_item["owner"]["mid"]


class ZhihuPage(Page):
    AccessBase = "https://www.zhihu.com/answer/"

    def __init__(self, page_item) -> None:
        super().__init__(page_item)

    def parse(self, page_item: dict):
        self.web_id = str(page_item["target"]["id"])
        self.access_url = self.AccessBase + self.web_id
        self.title = page_item["target"]["question"]["title"]
        self.ptype = "normal"
        self.user_name = page_item["target"]["author"]["name"]
        self.user_id = page_item["target"]["id"]
        self.excerpt = page_item["target"]["excerpt"]


class XhsPage(Page):
    AccessBase = "https://www.xiaohongshu.com/explore/"

    def __init__(self, page_item) -> None:
        super().__init__(page_item)
    
    def parse(self, page_item: dict):
        self.web_id = str(page_item["id"])
        self.access_url = self.AccessBase + self.web_id
        self.title = page_item["note_card"]["display_title"]
        self.ptype = page_item["note_card"]["type"]
        self.user_name = page_item["note_card"]["user"]["nickname"]
        self.user_id = page_item["note_card"]["user"]["user_id"]
