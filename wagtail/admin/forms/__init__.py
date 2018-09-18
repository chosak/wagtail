from importlib import import_module
import sys
import warnings

from wagtail.utils.deprecation import RemovedInWagtail25Warning

# definitions which are not being deprecated from wagtail.admin.forms
from .models import (  # NOQA
    FORM_FIELD_OVERRIDES, DIRECT_FORM_FIELD_OVERRIDES, formfield_for_dbfield, WagtailAdminModelFormMetaclass, WagtailAdminModelForm
)
from .pages import WagtailAdminPageForm  # NOQA


# Names previously defined here which now exist in submodules of wagtail.admin.forms:
#
# We want these to be available in this module during deprecation, but can't simply do
# `from .auth import *` or similar as this is susceptible to circular imports when importing
# any submodule (see https://github.com/wagtail/wagtail/issues/4515).
#
# As a workaround, we register a new custom importer for Python's module loading so that
# any attempts to load those deprecated names work properly while also producing a
# deprecation warning.

_MOVED_DEFINITIONS = {
    'LoginForm': 'wagtail.admin.forms.auth',
    'PasswordResetForm': 'wagtail.admin.forms.auth',

    'URLOrAbsolutePathValidator': 'wagtail.admin.forms.choosers',
    'URLOrAbsolutePathField': 'wagtail.admin.forms.choosers',
    'ExternalLinkChooserForm': 'wagtail.admin.forms.choosers',
    'EmailLinkChooserForm': 'wagtail.admin.forms.choosers',

    'CollectionViewRestrictionForm': 'wagtail.admin.forms.collections',
    'CollectionForm': 'wagtail.admin.forms.collections',
    'BaseCollectionMemberForm': 'wagtail.admin.forms.collections',
    'BaseGroupCollectionMemberPermissionFormSet': 'wagtail.admin.forms.collections',
    'collection_member_permission_formset_factory': 'wagtail.admin.forms.collections',

    'CopyForm': 'wagtail.admin.forms.pages',
    'PageViewRestrictionForm': 'wagtail.admin.forms.pages',

    'SearchForm': 'wagtail.admin.forms.search',

    'BaseViewRestrictionForm': 'wagtail.admin.forms.view_restrictions',
}


class _SubmoduleImporter:
    def __init__(self, name, moved_definitions):
        self.name = name
        self.moved_definitions = moved_definitions

    def find_module(self, fullname, path):
        if self._find_in_submodule(fullname):
            return self

    def load_module(self, fullname):
        try:
            return sys.modules[fullname]
        except KeyError:
            pass

        submodule_name, attr = self._find_in_submodule(fullname)

        submodule = import_module(submodule_name)

        # This shouldn't fail assuming that the list above contains
        # only references to valid submodule imports.
        imported = getattr(submodule, attr)

        warnings.warn(
            "%s has been moved from wagtail.admin.forms to %s" % (attr, submodule_name),
            category=RemovedInWagtail25Warning
        )

        sys.modules[fullname] = imported
        return imported

    def _find_in_submodule(self, fullname):
        if fullname.startswith(self.name + '.'):
            attr = fullname.split('.')[-1]

            if attr in self.moved_definitions:
                return self.moved_definitions[attr], attr


_importer = _SubmoduleImporter(__name__, _MOVED_DEFINITIONS)


# Make sure there's only ever one importer like this.
# Inspired by https://github.com/benjaminp/six/blob/edb7d0051202280d44939fd48863d244fe7b2c2b/six.py#L935
if sys.meta_path:
    for i, importer in enumerate(sys.meta_path):
        if (
            type(importer).__name__ == '_SubmoduleImporter' and
            importer.__name__ == __name__
        ):
            del sys.meta_path[i]
            break

        del i, importer


sys.meta_path.append(_importer)
