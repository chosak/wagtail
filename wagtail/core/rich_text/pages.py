from django.utils.html import escape

from wagtail.core.models import Page
from wagtail.core.rich_text import LinkHandler


class PageLinkHandler(LinkHandler):
    identifier = 'page'

    @staticmethod
    def get_model():
        return Page

    @classmethod
    def expand_db_attributes(cls, attrs):
        return cls.expand_db_attributes_many([attrs])[0]

    @classmethod
    def expand_db_attributes_many(cls, attrs_list):
        return [
            '<a href="%s">' % escape(page.specific.url)
            if page
            else "<a>"
            for page in cls.get_many(attrs_list)
        ]
