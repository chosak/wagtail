from django.utils.html import escape

from wagtail.core.rich_text import LinkHandler
from wagtail.documents import get_document_model

# Front-end conversion


class DocumentLinkHandler(LinkHandler):
    identifier = 'document'

    @staticmethod
    def get_model():
        return get_document_model()

    @classmethod
    def expand_db_attributes(cls, attrs):
        return cls.expand_db_attributes_many([attrs])[0]

    @classmethod
    def expand_db_attributes_many(cls, attrs_list):
        return [
            '<a href="%s">' % escape(doc.url)
            if doc
            else "<a>"
            for doc in cls.get_many(attrs_list)
        ]
