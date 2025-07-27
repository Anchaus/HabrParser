import random
import json
import requests
import datetime
from dataclasses import dataclass, asdict

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

class HabrParser:
    def __init__(self, json_file_name):
        ua = UserAgent()

        self.headers = {
            'accept': "application/json, text/plain, */*",
            'user-agent': ua.google
        }
        self.url = f"https://habr.com/ru/articles/"
        self.json_file_name = json_file_name

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
        name: str = None
        link: str = None
        rating: int = 0
        article_text: BeautifulSoup = None

        def _write_format(self):
            article = asdict(article)

            article.pop('name')
            if article['text'] == None:
                article.pop('text')
            
            return article


    def _parse_article_by_link(self, article: Article):
        article_html = requests.get(article.link, headers=self.headers).text
        article_soup = BeautifulSoup(article_html, 'lxml')

        rating_class = (
            'tm-votes-lever__score '
            'tm-votes-lever__score '
            'tm-votes-lever__score_appearance-article'
        )

        rating = article_soup.find(
            'div',
            class_=rating_class
        ).get_text()
        article.rating = int(rating)

        if article.rating <= -10 and article.text == None:
            article_text_class = (
                'tm-article-presenter__content '
                'tm-article-presenter__content_narrow'
            )
            article.article_text = article_soup.find(
                'article',
                class_=article_text_class
            )

        return article

    def _parse_article_from_page(self, article_soup: BeautifulSoup):
        article = self.Article()
        article.name = article_soup.find('span')
        article.link = f"https://habr.com{article_soup.get('href')}"

        # Check link is already in file
        # If true - stop parsing
        with open(self.json_file_name, 'r', encoding='utf-8') as file:
            saved_articles = json.load(file)
            if article.name in saved_articles.keys():
                return None
            
        return self._parse_article_by_link(article)

    def _parse_page(self, page_soup: BeautifulSoup):
        all_hrefs_articles = page_soup.find_all('a', class_='tm-title__link')
        article_dict = {}

        for article_soup in all_hrefs_articles[::-1]:
            article = self._parse_article_from_page(article_soup)
            
            # Found already saved article
            if article == None:
                break

            name = article.name
            article_dict[name] = article._write_format()

        return article_dict 

    def parse_habr(self):
        article_dict = {}
        page_html = requests.get(self.url, headers=self.headers).text
        page_soup = BeautifulSoup(page_html, 'lxml')

        article_dict.update(self._parse_page(page_soup))
        pages_count = page_soup.find_all(
            'a',
            class_="tm-pagination__page"
        )[-1]

        for page_num in range(1, pages_count + 1):
            url = self.url + f"page{page_num}/"
            page_html = requests(url, headers=self.headers)
            page_soup = BeautifulSoup(page_html, 'lxml')

            article_dict.update(self._parse_page(page_soup))

        with open(self.json_file_name, 'w', encoding='utf-8') as file:
            json.dump(article_dict, file)

    def update_articles(self, kind='all'):
        with open(self.json_file_name, 'r', encoding='utf-8') as file:
            saved_articles = json.load(file)
        
        for article_name, article in saved_articles.items():
            if kind == 'bad' and article['rating'] > 0:
                continue
            if kind == 'good' and article['rating'] < 0:
                continue

            article = self.Article(name=article_name, **article)
            article = self._parse_article_by_link(article)

            saved_articles[article_name] = article
        
        with open(self.json_file_name, 'w', encoding='utf-8') as file:
            json.dump(saved_articles, file)