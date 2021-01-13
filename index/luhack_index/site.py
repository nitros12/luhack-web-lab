from starlette.applications import Starlette
from starlette.requests import HTTPConnection

from luhack_index.templater import templates

app = Starlette()


@app.route("/")
async def index(request: HTTPConnection):
    return templates.TemplateResponse("main.j2", {"request": request})
