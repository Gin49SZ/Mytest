from aiohttp import web
from pathlib import Path
import jinja2

home_path = Path.cwd()
loader = jinja2.FileSystemLoader(str(home_path))
jinja_env = jinja2.Environment(loader=loader)


def jinjapage(j2file, **kwargs):
    page = jinja_env.get_template(j2file).render(kwargs)
    resp = web.Response(text=page, content_type="text/html")
    return resp
