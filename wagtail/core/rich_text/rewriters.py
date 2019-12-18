"""
Utility classes for rewriting elements of HTML-like strings
"""

import re
from collections import defaultdict

FIND_A_TAG = re.compile(r'<a(\b[^>]*)>')
FIND_EMBED_TAG = re.compile(r'<embed(\b[^>]*)/>')
FIND_ATTRS = re.compile(r'([\w-]+)\="([^"]*)"')


def extract_attrs(attr_string):
    """
    helper method to extract tag attributes, as a dict of un-escaped strings
    """
    attributes = {}
    for name, val in FIND_ATTRS.findall(attr_string):
        val = val.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&amp;', '&')
        attributes[name] = val
    return attributes


def extract_and_group_attrs(re_pattern, attr_string, grouping_fn):
    """Helper method to extract and group tag attributes.

    Returns a dict of {group_key: [(match, attrs), (match, attrs), ...]},
    where attrs are a dict of un-escaped strings.
    """
    grouped_attrs = defaultdict(list)

    for match in re_pattern.finditer(attr_string):
        attrs = extract_attrs(match.group(1))
        group_key = grouping_fn(attrs)
        grouped_attrs[group_key].append((match, attrs))

    return grouped_attrs


class TagRewriter:
    def __init__(self, rules):
        self.rules = rules

    def get_opening_tag_regex(self):
        raise NotImplementedError

    def get_tag_type_from_attrs(self, attrs):
        raise NotImplementedError

    def unsupported_tag_type_rule(self, attrs):
        """By default, tags with unsupported types are removed."""
        return ""

    def get_rule(self, tag_type):
        try:
            return self.rules[tag_type]
        except KeyError:
            return self.unsupported_tag_type_rule

    def __call__(self, html):
        matches_by_tag_type = extract_and_group_attrs(
            self.get_opening_tag_regex(),
            html,
            self.get_tag_type_from_attrs
        )

        offset = 0
        for tag_type in matches_by_tag_type.keys():
            rule = self.get_rule(tag_type)

            if not rule:
                continue

            for match, attrs in matches_by_tag_type[tag_type]:
                replacement_tag = rule(attrs)

                html = (
                    html[:match.start() + offset]
                    + replacement_tag
                    + html[match.end() + offset:]
                )

                offset += len(replacement_tag) - match.end() + match.start()

        return html


class EmbedRewriter(TagRewriter):
    def get_opening_tag_regex(self):
        return FIND_EMBED_TAG

    def get_tag_type_from_attrs(self, attrs):
        try:
            return attrs['embedtype']
        except KeyError:
            return None


class LinkRewriter(TagRewriter):
    def get_opening_tag_regex(self):
        return FIND_A_TAG

    def get_tag_type_from_attrs(self, attrs):
        try:
            return attrs['linktype']
        except KeyError:
            href = attrs.get('href', None)
            if href:
                # From href attribute we try to detect only the linktypes that we
                # currently support (`external` & `email`, `page` has a default handler)
                # from the link chooser.
                if href.startswith(('http:', 'https:')):
                    return 'external'
                elif href.startswith('mailto:'):
                    return 'email'
                elif href.startswith('#'):
                    return 'anchor'

            return None

    def unsupported_tag_type_rule(self, attrs):
        return "<a>"

    def get_rule(self, tag_type):
        if tag_type:
            try:
                return self.rules[tag_type]
            except KeyError:
                if tag_type not in ['email', 'external', 'anchor']:
                    return self.unsupported_tag_type_rule

        # We want to leave links untouched if they either provide no linktype
        # or if the linktypes they provide don't have a registered rule.
        return None


class MultiRuleRewriter:
    """Rewrites HTML by applying a sequence of rewriter functions"""
    def __init__(self, rewriters):
        self.rewriters = rewriters

    def __call__(self, html):
        for rewrite in self.rewriters:
            html = rewrite(html)
        return html
