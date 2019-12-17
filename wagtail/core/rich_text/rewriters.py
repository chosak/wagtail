"""
Utility classes for rewriting elements of HTML-like strings
"""

import re
import warnings
from functools import partial

from wagtail.core.utils import accepts_kwarg
from wagtail.utils.deprecation import RemovedInWagtail210Warning

FIND_A_TAG = re.compile(r'<a(\b[^>]*)>')
FIND_EMBED_TAG = re.compile(r'<embed(\b[^>]*)/>')
FIND_ATTRS = re.compile(r'([\w-]+)\="([^"]*)"')


def partial_with_context(fn, context):
    """Bind a context kwarg to a function, if the function supports it."""
    if accepts_kwarg(fn, 'context'):
        return partial(fn, context=context)
    else:
        warnings.warn(
            (
                "The rich text rewrite handler %s needs to be updated to "
                "accept an optional 'context' keyword argument"
            ) % fn.__qualname__,
            category=RemovedInWagtail210Warning
        )
        return fn


def extract_attrs(attr_string):
    """
    helper method to extract tag attributes, as a dict of un-escaped strings
    """
    attributes = {}
    for name, val in FIND_ATTRS.findall(attr_string):
        val = val.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&amp;', '&')
        attributes[name] = val
    return attributes


class EmbedRewriter:
    """
    Rewrites <embed embedtype="foo" /> tags within rich text into the HTML fragment given by the
    embed rule for 'foo'. Each embed rule is a function that takes a dict of attributes and
    returns the HTML fragment.
    """
    def __init__(self, embed_rules):
        self.embed_rules = embed_rules

    def replace_tag(self, match, context=None):
        attrs = extract_attrs(match.group(1))
        try:
            rule = self.embed_rules[attrs['embedtype']]
        except KeyError:
            # silently drop any tags with an unrecognised or missing embedtype attribute
            return ''
        return partial_with_context(rule, context)(attrs)

    def __call__(self, html, context=None):
        return FIND_EMBED_TAG.sub(
            partial(self.replace_tag, context=context),
            html
        )


class LinkRewriter:
    """
    Rewrites <a linktype="foo"> tags within rich text into the HTML fragment given by the
    rule for 'foo'. Each link rule is a function that takes a dict of attributes and
    returns the HTML fragment for the opening tag (only).
    """
    def __init__(self, link_rules):
        self.link_rules = link_rules

    def replace_tag(self, match, context=None):
        attrs = extract_attrs(match.group(1))
        try:
            link_type = attrs['linktype']
        except KeyError:
            link_type = None
            href = attrs.get('href', None)
            if href:
                # From href attribute we try to detect only the linktypes that we
                # currently support (`external` & `email`, `page` has a default handler)
                # from the link chooser.
                if href.startswith(('http:', 'https:')):
                    link_type = 'external'
                elif href.startswith('mailto:'):
                    link_type = 'email'
                elif href.startswith('#'):
                    link_type = 'anchor'

            if not link_type:
                # otherwise return ordinary links without a linktype unchanged
                return match.group(0)

        try:
            rule = self.link_rules[link_type]
        except KeyError:
            if link_type in ['email', 'external', 'anchor']:
                # If no rule is registered for supported types
                # return ordinary links without a linktype unchanged
                return match.group(0)
            # unrecognised link type
            return '<a>'

        return partial_with_context(rule, context)(attrs)

    def __call__(self, html, context=None):
        return FIND_A_TAG.sub(
            partial(self.replace_tag, context=context),
            html
        )


class MultiRuleRewriter:
    """Rewrites HTML by applying a sequence of rewriter functions"""
    def __init__(self, rewriters):
        self.rewriters = rewriters

    def __call__(self, html, context=None):
        for rewrite in self.rewriters:
            html = rewrite(html, context=context)
        return html
