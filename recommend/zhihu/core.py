# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/2 18:44
# @Desc    : B站爬虫

import asyncio
import os
import random
from asyncio import Task
from typing import Dict, List, Optional, Tuple

from playwright.async_api import (BrowserContext, BrowserType, Page,
                                  async_playwright)

from MediaCrawler import config
from MediaCrawler.base.base_crawler import AbstractCrawler
from MediaCrawler.proxy.proxy_ip_pool import IpInfoModel, create_ip_pool
from MediaCrawler.store import bilibili as bilibili_store
from MediaCrawler.tools import utils
from MediaCrawler.var import crawler_type_var

from .client import ZhihuClient
from .login import ZhihuLogin


class ZhihuRecommendCrawler(AbstractCrawler):
    context_page: Page
    bili_client: ZhihuClient
    browser_context: BrowserContext

    def __init__(self, num_note=20):
        self.index_url = "https://www.zhihu.com"
        self.user_agent = utils.get_user_agent()
        self.num_note = num_note

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
            self.zhihu_client = await self.create_zhihu_client(httpx_proxy_format)
            
            login_obj = ZhihuLogin(
                login_type=config.LOGIN_TYPE,
                login_phone="",  # your phone number
                browser_context=self.browser_context,
                context_page=self.context_page,
                cookie_str=config.COOKIES
            )
            await login_obj.begin()
            await self.zhihu_client.update_cookies(browser_context=self.browser_context)

            crawler_type_var.set(config.CRAWLER_TYPE)

            recommend_note = []
            while len(recommend_note) < self.num_note:
                new_note = await self.recommend()
                recommend_note += new_note
            recommend_note = recommend_note[:self.num_note]

            utils.logger.info(
                "[Zhihu.start] Zhihu Crawler finished ...")
            return recommend_note
            
    async def launch_browser(
        self,
        chromium: BrowserType,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True
    ) -> BrowserContext:
        """Launch browser and create browser context"""
        utils.logger.info(
            "[BilibiliCrawler.launch_browser] Begin create browser context ...")
        if config.SAVE_LOGIN_STATE:
            # feat issue #14
            # we will save login state to avoid login every time
            user_data_dir = os.path.join(os.getcwd(), "browser_data",
                                         config.USER_DATA_DIR % config.PLATFORM)  # type: ignore
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                proxy=playwright_proxy,  # type: ignore
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent
            )
            return browser_context
        else:
            # type: ignore
            browser = await chromium.launch(headless=headless, proxy=playwright_proxy)
            browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent
            )
            return browser_context
        
    async def recommend(self):
        res_recommend = await self.zhihu_client.get_recommend()
        # utils.logger.info("Zhihu searcher not implemented.")
        return res_recommend
    
    async def search(self):
        raise NotImplementedError
        
    async def create_zhihu_client(self, httpx_proxy: Optional[str]) -> ZhihuClient:
        """Create xhs client"""
        cookie_str, cookie_dict = utils.convert_cookies(await self.browser_context.cookies())
        zhihu_client_obj = ZhihuClient(
            proxies=httpx_proxy,
            headers={
                "User-Agent": self.user_agent,
                "Cookie": cookie_str,
                "Origin": "https://www.zhihu.com",
                "Referer": "https://www.zhihu.com",
                "Content-Type": "application/json;charset=UTF-8"
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
        )
        return zhihu_client_obj