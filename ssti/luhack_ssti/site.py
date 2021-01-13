import os
from pathlib import Path

from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection
from starlette.routing import Mount, Router
from wtforms import Form, StringField, TextAreaField

from luhack_ssti.templater import templates

load_dotenv()

root_dir = Path(__file__).parent

with open(root_dir.parent / "flag.txt", "w") as f:
    f.write(os.getenv("SSTI_FLAG"))

router = Router()

class PostForm(Form):
    name = StringField("Name")
    message = TextAreaField("Message")


@router.route("/")
async def index(request: HTTPConnection):
    posts = request.session.get("posts")
    if posts is None:
        posts = []
        request.session["posts"] = posts

    form = PostForm()

    return templates.TemplateResponse(
        "main.j2",
        {
            "request": request,
            "form": form,
            "posts": posts,
            "post_create": request.url_for("post"),
        },
    )


@router.route("/post", methods=["POST"])
async def post(request: HTTPConnection):
    form = await request.form()
    form = PostForm(form)

    name = form.name.data
    message = form.message.data

    posts = request.session.get("posts")
    if posts is None:
        posts = []
        request.session["posts"] = posts

    posts.append((name, message))

    return templates.TemplateResponse(
        "main.j2",
        {
            "request": request,
            "form": form,
            "posts": posts,
            "post_create": request.url_for("post"),
        },
    )


app = Starlette(routes=[Mount("/ssti", app=router)])

app.add_middleware(SessionMiddleware, secret_key="doesntmatter")
