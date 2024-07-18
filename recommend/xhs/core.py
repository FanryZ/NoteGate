from typing import Dict, List, Optional, Tuple

from playwright.async_api import (BrowserContext, BrowserType, Page,
                                  async_playwright)

from MediaCrawler import config
from MediaCrawler.proxy.proxy_ip_pool import IpInfoModel, create_ip_pool
from MediaCrawler.tools import utils
from MediaCrawler.var import crawler_type_var

from MediaCrawler.media_platform.xhs.client import XiaoHongShuClient
from MediaCrawler.media_platform.xhs.login import XiaoHongShuLogin
from MediaCrawler.media_platform.xhs import XiaoHongShuCrawler


async def get_recommend(xhs_client: XiaoHongShuClient, num: int = 40):
    """
    KuaiShou web search api
    :param keyword: 搜索关键词
    :param page: 分页参数具体第几页
    :param page_size: 每一页参数的数量
    :param order: 搜索结果排序，默认位综合排序
    :return:
    """
    uri = "/api/sns/web/v1/homefeed"
    data = {
        "num": num
    }
    return await xhs_client.post(uri, data)


class XiaoHongShuRecommendCrawler(XiaoHongShuCrawler):
    
    def __init__(self, num_note=20) -> None:
        super().__init__()
        self.num_note = num_note

    async def start(self) -> None:
        playwright_proxy_format, httpx_proxy_format = None, None
        if config.ENABLE_IP_PROXY:
            ip_proxy_pool = await create_ip_pool(config.IP_PROXY_POOL_COUNT, enable_validate_ip=True)
            ip_proxy_info: IpInfoModel = await ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = self.format_proxy_info(ip_proxy_info)

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
            # add a cookie attribute webId to avoid the appearance of a sliding captcha on the webpage
            await self.browser_context.add_cookies([{
                'name': "webId",
                'value': "xxx123",  # any value
                'domain': ".xiaohongshu.com",
                'path': "/"
            }])
            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(self.index_url)

            # Create a client to interact with the xiaohongshu website.
            self.xhs_client = await self.create_xhs_client(httpx_proxy_format)
            if not await self.xhs_client.pong():
                login_obj = XiaoHongShuLogin(
                    login_type=config.LOGIN_TYPE,
                    login_phone="",  # input your phone number
                    browser_context=self.browser_context,
                    context_page=self.context_page,
                    cookie_str=config.COOKIES
                )
                await login_obj.begin()
                await self.xhs_client.update_cookies(browser_context=self.browser_context)

            crawler_type_var.set(config.CRAWLER_TYPE)
            
            recommend_note = []
            while len(recommend_note) < self.num_note:
                new_note = await get_recommend(self.xhs_client, self.num_note)
                recommend_note += new_note["items"]
            recommend_note = recommend_note[:self.num_note]

            utils.logger.info("[XiaoHongShuCrawler.start] Xhs Crawler finished ...")
            return recommend_note

