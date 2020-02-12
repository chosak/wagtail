from wagtail.core.rich_text import EmbedHandler
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format


# Front-end conversion

class ImageEmbedHandler(EmbedHandler):
    identifier = 'image'

    @staticmethod
    def get_model():
        return get_image_model()

    @classmethod
    def expand_db_attributes(cls, attrs):
        return cls.expand_db_attributes_many([attrs])[0]

    @classmethod
    def expand_db_attributes_many(cls, attrs_list):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation for use on the front-end.
        """
        images = cls.get_many(attrs_list)

        tags = []
        for attrs, image in zip(attrs_list, images):
            if image:
                image_format = get_image_format(attrs['format'])
                tag = image_format.image_to_html(image, attrs.get('alt', ''))
            else:
                tag = '<img alt="">'

            tags.append(tag)

        return tags
