#! /usr/bin/env python

from .. import config
from ..habr_parser import HabrParser

def main():
    parser = HabrParser(config.JSON_FILE_PATH)
    parser.update_articles(kind='all')
    parser.parse_habr()

if __name__ == '__main__':
    main()