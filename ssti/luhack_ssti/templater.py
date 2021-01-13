from jinja2 import contextfilter, Template, Markup
from starlette.templating import Jinja2Templates

from pathlib import Path

@contextfilter
def dangerous_render(context, value):
    try:
        return Template(value).render(context)
    except Exception as e:
        return str(e)

root_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(root_dir / "templates"))
templates.env.filters["dangerous_render"] = dangerous_render
