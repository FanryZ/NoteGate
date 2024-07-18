import asyncio
import sys
import numpy as np
import argparse
sys.path.append("./MediaCrawler")

from MediaCrawler import config

from MediaCrawler.base.base_crawler import AbstractCrawler
from recommend.bilibili import BilibiliRecommendCrawler
from recommend.zhihu import ZhihuRecommendCrawler
from recommend.xhs import XiaoHongShuRecommendCrawler

from utils import page, db
from utils.config import NoteGateConfig
from utils.tokens import tokenize
from utils.classfier import TokenClassfier

from quart import Quart, render_template, jsonify, request, redirect, url_for


class CrawlerFactory:
    CRAWLERS = {
        "bili": BilibiliRecommendCrawler,
        "zhihu": ZhihuRecommendCrawler,
        "xhs": XiaoHongShuRecommendCrawler
    }

    @staticmethod
    def create_crawler(platform: str, num_note) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError("Invalid Media Platform Currently only supported zhihu or bilibili.")
        return crawler_class(num_note)

PAGES = {
    "bili": page.BiliPage,
    "zhihu": page.ZhihuPage,
    "xhs": page.XhsPage
}


shown_notes = None
cache_notes = None
recommend_notes = None
token_classifier = TokenClassfier()

async def get_data(show=False, cookie=True):
    global cache_notes, shown_notes
    num_note = NoteGateConfig.num_note
    config.LOGIN_TYPE = "cookie" if cookie else "qrcode"
    if config.SAVE_DATA_OPTION == "db":
        await db.init_db()

    all_pages = []
    for platform in NoteGateConfig.platforms:
        crawler = CrawlerFactory.create_crawler(platform=platform, num_note=num_note)
        pager = PAGES[platform]
        result = await crawler.start()
        pages = [pager(raw_page) for raw_page in result]
        all_pages += pages

        # if config.SAVE_DATA_OPTION == "db":
        #     await db.close()
    for p in all_pages:
        tokens = tokenize(p)
        p.tokens = tokens
    cache_notes = all_pages
    if show:
        shown_notes = cache_notes

async def fit_classfier():
    token_classifier.reset()
    data_pairs = db.get_token_pro()
    tokens, pros = [pair[0] for pair in data_pairs], [pair[1] for pair in data_pairs]
    token_classifier.tokenize_fit(tokens, pros)

async def get_notes_and_fit(show=False):
    await get_data(show=show)
    await fit_classfier()

def topk():
    global recommend_notes
    predictions = token_classifier.infer([p.tokens for p in shown_notes])
    num_recommend = NoteGateConfig.num_recommend
    recommend_notes = [shown_notes[idx] for idx in np.argsort(predictions)[-1:-num_recommend-1:-1]]


app = Quart(__name__)

@app.before_serving
async def startup():
    asyncio.create_task(get_notes_and_fit(show=True))

@app.route('/')
async def index():
    global shown_notes
    shown_notes = cache_notes
    topk()
    top_notes = [
        {
            "index": index,
            "author": note.user_name,
            "excerpt": note.excerpt if note.excerpt else "",
            "title": note.title,
            "link": note.access_url
        } for index, note in enumerate(recommend_notes)
    ]
    asyncio.create_task(get_notes_and_fit(show=False))
    return await render_template('index.html', notes=top_notes)

@app.route('/feedback', methods=['POST'])
async def feedback():
    data = await request.json
    pro = data['pro']
    p = recommend_notes[int(data['index'])]
    print("Author: {}; Title: {};, Url: {}; Pro: {}\nTokens: {}"
          .format(p.user_name, p.title, p.access_url, pro, p.tokens))
    
    db.insert(p, p.tokens, pro)
    db.conn.commit()
    return jsonify({"status": "success"})

@app.route('/refresh', methods=['POST'])
async def refresh():
    global shown_notes
    shown_notes = cache_notes
    asyncio.create_task(get_notes_and_fit(show=False))
    return redirect(url_for('index'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-cookie", action="store_true", default=False)
    args = parser.parse_args()
    if args.no_cookie:
        asyncio.run(get_data(cookie=False))
    else:
        app.run(debug=True, port=5000)

