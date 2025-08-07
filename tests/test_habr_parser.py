import os
from typing import overload

import pytest

from src.habr_parser import HabrParser


# ============================================================================
# Habr Parser
# ============================================================================


class HabrParserTester(HabrParser):
    @overload
    def __init__(
        self,
        json_file_name,
        content_type='article'
    ):
        super().__init__(
            json_file_name=json_file_name,
            content_type=content_type
        )

        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        self.url = f"{script_dir}/data/{content_type}.html"

    @overload
    async def _get_response(self, url):
        with open(self.url) as html_file:
            html_page = html_file.read()

        return html_page