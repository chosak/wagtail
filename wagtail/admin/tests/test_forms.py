import types

from django.forms.fields import CharField
from django.test import TestCase

from wagtail.admin.forms.auth import LoginForm


class CustomLoginForm(LoginForm):
    captcha = CharField(
        label='Captcha', help_text="should be in extra_fields()")


class TestLoginForm(TestCase):

    def test_extra_fields(self):
        form = CustomLoginForm()
        self.assertEqual(list(form.extra_fields), [
            ('captcha', form.fields['captcha'])
        ])


class TestFormSubmoduleImports(TestCase):
    def test_import_module_still_valid(self):
        import wagtail.admin.forms
        self.assertIsInstance(wagtail.admin.forms, types.ModuleType)

    def test_deprecated_import_from_submodule(self):
        try:
            from wagtail.admin.forms import LoginForm  # noqa
        except ImportError:
            self.fail("deprecated imports should still work")

    def test_valid_import_from_submodule(self):
        try:
            from wagtail.admin.forms.auth import LoginForm  # noqa
        except ImportError:
            self.fail("imports from submodules should still work")

    def test_invalid_imports_from_module_raise_importerror(self):
        with self.assertRaises(ImportError):
            from wagtail.admin.forms import FooBar  # noqa

    def test_invalid_imports_from_submodule_raise_importerror(self):
        with self.assertRaises(ImportError):
            from wagtail.admin.forms.auth import FooBar  # noqa
