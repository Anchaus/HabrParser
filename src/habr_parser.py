from dataclasses import dataclass, asdict
import datetime
import json

from aiohttp import ClientSession
import asyncio
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# TODO: Make posts and news parse logic
class HabrParser:
    def __init__(
        self,
        json_file_name, # TODO: Change to database logic
        content_type='article'
    ):
        ua = UserAgent()

        self.headers = {
            'accept': "application/json, text/plain, */*",
            'user-agent': ua.google
        }
        self.content_type = content_type

        if content_type != 'article':
            raise ValueError(
                "HabrParser can't handle posts and news in this version"
            )
        self.url = f"https://habr.com/ru/{content_type}/"
        self.json_file_name = json_file_name

    # TODO: Change to database query
    def _write_json(self, new_json_data):
        with open(self.json_file_name, 'r', encoding='utf-8') as file:
            old_json_data = json.load(file)
        
        for key, value in old_json_data.items():
            if key not in new_json_data:
                new_json_data[key] = value

        with open(self.json_file_name, 'w', encoding='utf-8') as file:
            json.dump(new_json_data, file)


    @dataclass
    class Article:
        id: int = None
        author_link: str = None
        title: str = None
        article_link: str = None
        rating: int = 0
        timestamp: datetime.datetime = None
        text: BeautifulSoup = None

        def _write_format(self):
            article = asdict(article)

            article.pop('id')
            if article['text'] == None:
                article.pop('text')
            
            return article

    
    async def _get_response(self, url):
        async with ClientSession() as session:
            async with session.get(url=url,
                                   headers=self.headers) as resp:
                # TODO: Handle and log errors
                if resp.status != 200:
                    pass
                html_page = await resp.text()

        return html_page

    async def _update_article(self, article):
        article_html = await self._get_response(article.article_link)
        article_soup = BeautifulSoup(article_html, 'lxml')

        rating_class = (
        'tm-votes-lever__score ',
        'tm-votes-lever__score_appearance-article ',
        'tm-votes-lever__score'
        )
        article.rating = article_soup.find(
            'div',
            class_=rating_class
        ).get_text()

        if article.rating <= -10 and article.text == None:
            text_class = (
                'article-formatted-body ',
                'article-formatted-body ',
                'article-formatted-body_version-2'
            )
            article.text = article_soup.find(
                'div',
                class_=text_class
            )
    
    async def _parse_article_from_page(self, article_soup: BeautifulSoup):
        article = self.Article()
        article.id = article_soup.get('id')

        author_soup = article_soup.find('a', class_='tm-user-info__username')
        article.author_link = f"https://habr.com{author_soup.get('href')}"

        title_soup = article_soup.find('a', class_='tm-title__link')
        article.title = title_soup.find('span').get_text()
        article.article_link = f"https://habr.com{title_soup.get('href')}"
        
        # ISO format timestamp
        timestamp = article_soup.find('time').get('datetime')
        article.timestamp = datetime.fromisoformat(timestamp)

        rating_class = (
            'tm-votes-meter__value ',
            'tm-votes-meter__value ',
            'tm-votes-meter__value_appearance-article ',
            'tm-votes-meter__value_rating'
        )
        article.rating = article_soup.find(
            'span',
            class_=rating_class
        ).get_text()

        if article.rating <= -10:
            article_html = await self._get_response(article.article_link)

            text_soup = BeautifulSoup(article_html, 'lxml')
            text_class = (
                'article-formatted-body ',
                'article-formatted-body ',
                'article-formatted-body_version-2'
            )
            article.text = text_soup.find(
                'div',
                class_=text_class
            )

        # TODO: Check article.timestamp > last timestamp in database
        if False:
            return None
            
        return article

    async def _parse_page(self, page_soup: BeautifulSoup):
        all_hrefs_articles = page_soup.find_all(
            'article',
            class_='tm-articles-list__item'
        )
        article_dict = {}

        for article_soup in all_hrefs_articles[::-1]:
            article = self._parse_article_from_page(article_soup)
            
            # Found already saved article
            if article == None:
                break

            name = article.name
            article_dict[name] = article._write_format()

        return article_dict

    async def _get_habr_page(self, url):
        page_html = await self._get_response(url)
        page_soup = BeautifulSoup(page_html, 'lxml')

        return self._parse_page(page_soup)

    async def parse_habr(self):
        async def async_work():
            article_dict = {}
            tasks = []

            # Go through habr pages (const 1-50)
            for page_num in range(1, 51):
                url = self.url + f"page{page_num}/"
                tasks.append(asyncio.create_task(self._get_habr_page(url)))

            results = await asyncio.gather(*tasks)

            for result in results:
                article_dict.update(result)

            # TODO: Change to database query
            with open(self.json_file_name, 'w', encoding='utf-8') as file:
                json.dump(article_dict, file)
        
        asyncio.run(async_work())

    async def update_articles(self, kind='all'):
        # TODO: Change to database query
        with open(self.json_file_name, 'r', encoding='utf-8') as file:
            saved_articles = json.load(file)
        
        for article_name, article in saved_articles.items():
            if kind == 'bad' and article['rating'] > 0:
                continue
            if kind == 'good' and article['rating'] < 0:
                continue

            article = self.Article(name=article_name, **article)

            article = self.update_article(article)

            saved_articles[article_name] = article
        
        # TODO: Change to database query
        with open(self.json_file_name, 'w', encoding='utf-8') as file:
            json.dump(saved_articles, file)