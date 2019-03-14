from django.template.loader import render_to_string
from django.utils.functional import cached_property

from wagtail.admin.compare import BlockComparison
from wagtail.core.blocks import ChooserBlock
from wagtail.core.blocks import ChooserBlock, IntegerBlock, StructBlock

from .shortcuts import get_rendition_or_not_found


class ImageChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        from wagtail.images import get_image_model
        return get_image_model()

    @cached_property
    def widget(self):
        from wagtail.images.widgets import AdminImageChooser
        return AdminImageChooser

    def render_basic(self, value, context=None):
        if value:
            return get_rendition_or_not_found(value, 'original').img_tag()
        else:
            return ''

    def get_comparison_class(self):
        return ImageChooserBlockComparison

    class Meta:
        icon = "image"


class ImageChooserBlockComparison(BlockComparison):
    def htmlvalue(self, val):
        return render_to_string("wagtailimages/widgets/compare.html", {
            'image_a': val,
            'image_b': val,
        })

    def htmldiff(self):
        return render_to_string("wagtailimages/widgets/compare.html", {
            'image_a': self.val_a,
            'image_b': self.val_b,
        })


# HT START
class SelectCropChooserBlock(ImageChooserBlock):
    @cached_property
    def widget(self):
        from .widgets import SelectCropAdminImageChooser
        return SelectCropAdminImageChooser


class SelectCropBlock(StructBlock):

    # using get_context to add things to the context at run time and then checking for appropriate values in the context in the images tag
    # Note that if the image value of this block is passed to the image tag directly by another block
    # e.g. `image value.my_field_referencing_this_block.image max-300x200`, this block's get_context isn't called and hence cropping doesn't work.
    # This block must render itself and an image spec template should be passed to it in the constructor.
    # If we wrote a special template tag to allow variables to be passed to a spec filter they could also write something like:
    # `crop_image_tag value.field_ref_this_block.image value.field-ref_this_block.focal_point_x value.field-ref_this_block.focal_point_y \
    # value.field-ref_this_block.focal_point_width value.field-ref_this_block.focal_point_height | other_filters_string`
    # but its a bit ponderous and in general it seems better applying crop values automatically if they've been selected in the admin.
    # All in all asking the consumer to specify a simple template to the constructor is the best I've come up with so far.
    # Open to better ideas

    image = SelectCropChooserBlock(required=True)
    focal_point_x = IntegerBlock(required=False, group="hidden-input", label="focal_point_x")
    focal_point_y = IntegerBlock(required=False, group="hidden-input", label="focal_point_y")
    focal_point_width = IntegerBlock(required=False, group="hidden-input", label="focal_point_width")
    focal_point_height = IntegerBlock(required=False, group="hidden-input", label="focal_point_height")

    select_area_x = IntegerBlock(required=False, group="hidden-input", label="select_area_x")
    select_area_y = IntegerBlock(required=False, group="hidden-input", label="select_area_y")
    select_area_width = IntegerBlock(required=False, group="hidden-input", label="select_area_width")
    select_area_height = IntegerBlock(required=False, group="hidden-input", label="select_area_height")

    def add_area_info(self, value, context):
        area_labels = ['select_area_x', 'select_area_y', 'select_area_width', 'select_area_height']

        if context.get('children'):
            for name, block in context['children'].items():
                if name in area_labels:
                    if not isinstance(block.value, int):
                        print("{} not an int".format(block.value))
                        old_name = name.replace('select_area', 'focal_point')
                        block.value = context['children'].get(old_name)  # updates the block value (which will now be picked up in the crop_etc fields of the form and hence the jcrop api)
                        value[name] = block.value  # updates the parrallel StructValues that wagtail provides
                    context[name] = block.value  # makes these same values available directly in the template context
        else:  # we're not in the admin as children isn't populated...
            for name in area_labels:
                v = value.get(name)
                if not isinstance(v, int):
                    v = value.get(name.replace('select_area', 'focal_point'))
                context[name] = v

        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # here we're copying the values from the focal_etc blocks to the crop_ blocks purely for the purposes of preserving the data automatically
        # this whole block can be lost along with the focal_ fields once the pages have been loaded and saved...
        # the entire function can be swopped for the lines below...
        # area_labels = ['select_area_x', 'select_area_y', 'select_area_width', 'select_area_height']
        # for name in area_labels:
        #     context[name] = value.get(name)

    def render_basic(self, value, context=None):
        # this will be invoked if no template value is defined on the Meta
        context = super().get_context(value)
        self.add_area_info(value, context)
        image = value.get('image')
        if image:
            crop_specs = [context['select_area_x'], context['select_area_y'], context['select_area_width'], context['select_area_height']]
            if all(v is not None for v in crop_specs):
                select_spec = "crop-" + str(context['select_area_x']) + ":" + str(context['select_area_y']) + ":" + str(context['select_area_width']) + ":" + str(context['select_area_height'])
                return get_rendition_or_not_found(image, select_spec).img_tag()
            else:
                return get_rendition_or_not_found(image, 'original').img_tag()
        else:
            return ''

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        self.add_area_info(value, context)
        return context

    def get_form_context(self, value, prefix='', errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        self.add_area_info(value, context)
        return context

    class Meta:
        icon = "image"
        # template = "wagtailimages/widgets/select_crop_block_default.html" # while this is commented out render_basic takes over
        form_classname = "select-crop-image-block struct-block"
        form_template = "wagtailimages/widgets/select_crop_block.html"
# HT END
