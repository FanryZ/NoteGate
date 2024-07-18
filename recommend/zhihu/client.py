# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/2 18:44
# @Desc    : bilibili 请求客户端
import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urlencode

import httpx
from playwright.async_api import BrowserContext, Page

from MediaCrawler.base.base_crawler import AbstractApiClient
from MediaCrawler.tools import utils
from .exception import DataFetchError

""""https://www.zhihu.com/api/v3/feed/topstory/recommend"""

class ZhihuClient(AbstractApiClient):
    def __init__(
            self,
            timeout=10,
            proxies=None,
            *,
            headers: Dict[str, str],
            playwright_page: Page,
            cookie_dict: Dict[str, str],
    ):
        self.proxies = proxies
        self.timeout = timeout
        self.headers = headers
        self._host = "https://www.zhihu.com"
        self.playwright_page = playwright_page
        self.cookie_dict = cookie_dict

    async def request(self, method, url, **kwargs) -> Any:
        async with httpx.AsyncClient(proxies=self.proxies) as client:
            response = await client.request(
                method, url, timeout=self.timeout,
                **kwargs
            )
        data: Dict = response.json()
        # if data.get("code") != 0:
        #     raise DataFetchError(data.get("message", "unkonw error"))
        # else:
        return data.get("data", {})

    async def get(self, uri: str, params=None, enable_params_sign: bool = True) -> Dict:
        final_uri = uri
        # if enable_params_sign:
        #     params = await self.pre_request_data(params)
        if isinstance(params, dict):
            final_uri = (f"{uri}?"
                         f"{urlencode(params)}")
        return await self.request(method="GET", url=f"{self._host}{final_uri}", headers=self.headers)

    async def update_cookies(self, browser_context: BrowserContext):
        pass
    
    async def get_recommend(self):
        uri = "/api/v3/feed/topstory/recommend"
        data = {
        }
        return await self.get(uri, data)