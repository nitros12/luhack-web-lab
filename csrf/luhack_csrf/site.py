import os
from collections import defaultdict
from pathlib import Path

from starlette.exceptions import HTTPException

import aiohttp
from dotenv import load_dotenv
from furl import furl
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection
from starlette.responses import RedirectResponse
from starlette.routing import Mount, Router
from wtforms import Form, StringField, IntegerField

from luhack_csrf.templater import templates

load_dotenv()

flag = os.getenv("CSRF_FLAG")

root_dir = Path(__file__).parent

router = Router()

class ClickForm(Form):
    link = StringField("link")


@router.route("/")
async def index(request: HTTPConnection):
    return templates.TemplateResponse("main.j2", {"request": request})

def redirect_response(*args, **kwargs):
    kwargs.setdefault("status_code", 303)
    return RedirectResponse(*args, **kwargs)

@router.route("/kerry")
class Kerry(HTTPEndpoint):
    async def get(self, request: HTTPConnection):
        form = ClickForm()

        return templates.TemplateResponse(
            "kerry.j2", {"request": request, "form": form}
        )

    async def post(self, request: HTTPConnection):
        form = await request.form()
        form = ClickForm(form)

        link = furl(form.link.data)

        if link.path.segments and link.path.segments[0] == "csrf":
            link.netloc = "csrf:8080"

        cookies = {"username": flag}

        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(link.url) as response:
                print(response.status)

        return templates.TemplateResponse(
            "kerry.j2", {"request": request, "form": form}
        )


transactions = defaultdict(list)


class LoginForm(Form):
    user = StringField("Username")

class TransferForm(Form):
    dest = StringField("Destination")
    amount = IntegerField("Amount")


@router.route("/bank")
async def bank(request: HTTPConnection):
    login_form = LoginForm()
    transfer_form = TransferForm()

    current_user = request.cookies.get("username")

    return templates.TemplateResponse(
        "bank.j2",
        {
            "request": request,
            "login_form": login_form,
            "transfer_form": transfer_form,
            "login_url": request.url_for("bank_login"),
            "transfer_url": request.url_for("bank_transfer"),
            "current_user": current_user,
            "transactions": [] if current_user is None else transactions[current_user],
        },
    )


@router.route("/bank/login", methods=["POST"])
async def bank_login(request: HTTPConnection):
    form = await request.form()
    form = LoginForm(form)

    r = redirect_response(url=request.url_for("bank"))
    r.set_cookie("username", form.user.data)

    return r

@router.route("/bank/transfer", methods=["GET", "POST"])
async def bank_transfer(request: HTTPConnection):
    form = TransferForm(request.query_params)

    if not form.validate():
        login_form = LoginForm()

        current_user = request.cookies.get("username")

        return templates.TemplateResponse(
            "bank.j2",
            {
                "request": request,
                "login_form": login_form,
                "transfer_form": form,
                "login_url": request.url_for("bank_login"),
                "transfer_url": request.url_for("bank_transfer"),
                "current_user": current_user,
                "transactions": [] if current_user is None else transactions[current_user],
            },
        )

    from_ = request.cookies.get("username")
    if from_ is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    transaction = (from_, form.dest.data, form.amount.data)

    print(transaction)

    transactions[form.dest.data].append(transaction)
    transactions[from_].append(transaction)

    return redirect_response(url=request.url_for("bank"))


app = Starlette(routes=[
    Mount("/csrf", app=router)
])

app.add_middleware(SessionMiddleware, secret_key="doesntmatter")
