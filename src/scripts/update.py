#!/usr/bin/env python

from sys import argv

from ..habr_parser import HabrParser
from .. import config

def main():
    parser = HabrParser(config.JSON_FILE_PATH)
    parser.update_articles(argv[1])

if __name__ == '__main__':
    main()