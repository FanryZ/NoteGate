# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/2 18:44
# @Desc    : B站爬虫

from typing import Dict, List
from playwright.async_api import async_playwright

from MediaCrawler.media_platform.bilibili.field import SearchOrderType
from MediaCrawler.media_platform.bilibili.core import BilibiliCrawler
from MediaCrawler.media_platform.bilibili.client import BilibiliClient
from MediaCrawler.tools import utils
from MediaCrawler import config

from MediaCrawler.proxy.proxy_ip_pool import IpInfoModel, create_ip_pool
from MediaCrawler.tools import utils
from MediaCrawler.var import crawler_type_var
from MediaCrawler.media_platform.bilibili.login import BilibiliLogin


async def get_recommend(bilibili_client: BilibiliClient, page_size: int = 14):
    """
    KuaiShou web search api
    :param keyword: 搜索关键词
    :param page: 分页参数具体第几页
    :param page_size: 每一页参数的数量
    :param order: 搜索结果排序，默认位综合排序
    :return:
    """
    uri = "/x/web-interface/index/top/rcmd"
    post_data = {
        "ps": page_size,
    }
    return await bilibili_client.get(uri, post_data)


class BilibiliRecommendCrawler(BilibiliCrawler):

    def __init__(self, num_note=20):
        super().__init__()
        self.num_note = num_note

    async def recommend(self):
        """
        search bilibili video with keywords
        :return:
        """
        utils.logger.info(
            "[BilibiliCrawler.search] Begin get bilibli recommendations")
        recommendations = await get_recommend(
            self.bili_client,
            page_size = 14
        )
        return recommendations
        
    async def start(self):
        playwright_proxy_format, httpx_proxy_format = None, None
        if config.ENABLE_IP_PROXY:
            ip_proxy_pool = await create_ip_pool(config.IP_PROXY_POOL_COUNT, enable_validate_ip=True)
            ip_proxy_info: IpInfoModel = await ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = self.format_proxy_info(
                ip_proxy_info)

        async with async_playwright() as playwright:
            # Launch a browser context.
            chromium = playwright.chromium
            self.browser_context = await self.launch_browser(
                chromium,
                None,
                self.user_agent,
                headless=config.HEADLESS
            )
            # stealth.min.js is a js script to prevent the website from detecting the crawler.
            await self.browser_context.add_init_script(path="libs/stealth.min.js")
            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(self.index_url)

            # Create a client to interact with the xiaohongshu website.
            self.bili_client = await self.create_bilibili_client(httpx_proxy_format)
            if not await self.bili_client.pong():
                login_obj = BilibiliLogin(
                    login_type=config.LOGIN_TYPE,
                    login_phone="",  # your phone number
                    browser_context=self.browser_context,
                    context_page=self.context_page,
                    cookie_str=config.COOKIES
                )
                await login_obj.begin()
                await self.bili_client.update_cookies(browser_context=self.browser_context)

            crawler_type_var.set(config.CRAWLER_TYPE)

            recommend_note = []
            while len(recommend_note) < self.num_note:
                new_note = await self.recommend()
                recommend_note += new_note["item"]
            recommend_note = recommend_note[:self.num_note]

            utils.logger.info(
                "[BilibiliCrawler.start] Bilibili Crawler finished ...")
            return recommend_note
