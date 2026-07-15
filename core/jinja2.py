from django.templatetags.static import static
from django.urls import reverse
from django.middleware.csrf import get_token
from jinja2 import Environment
from markupsafe import Markup

from core.image_defaults import placeholder_image_url
from core.category_icons import footer_category_columns, hero_category_items
from users.industries import INDUSTRY_GROUPS


def environment(**options):
    env = Environment(**options)

    def csrf_input(request):
        return Markup(f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">')

    def csrf_token(request):
        return get_token(request)

    env.globals.update({
        'static': static,
        'url': reverse,
        'csrf_field': csrf_input,
        'csrf_token_value': csrf_token,
        'industry_groups': INDUSTRY_GROUPS,
        'hero_categories': hero_category_items(),
        'footer_category_columns': footer_category_columns(),
        'placeholder_image': placeholder_image_url(),
    })
    return env
