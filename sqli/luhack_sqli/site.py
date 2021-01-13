import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.requests import HTTPConnection
from starlette.routing import Mount, Router
from wtforms import Form, StringField
from wtforms.fields import PasswordField

from luhack_sqli.templater import templates

load_dotenv()

db_url = os.getenv("DB_URL")

root_dir = Path(__file__).parent

router = Router()

pool = None


class LoginForm(Form):
    user = StringField("Username")
    password = PasswordField("Password")


@router.route("/")
class Index(HTTPEndpoint):
    async def get(self, request: HTTPConnection):
        form = LoginForm()

        return templates.TemplateResponse("main.j2", {"request": request, "form": form})

    async def post(self, request: HTTPConnection):
        form = await request.form()
        form = LoginForm(form)

        user = form.user.data
        password = form.password.data

        async with pool.acquire() as con:
            result = await con.fetch(
                f"""
                SELECT username FROM users WHERE username = '{user}' and password = '{password}'
            """
            )
            r = "\n".join(" ".join(map(str, r)) for r in result)
            if not r:
                r = "No user with that username or password found"
            else:
                r = f"Welcome: {r}"

            form.user.errors = (r,)

            return templates.TemplateResponse(
                "main.j2", {"request": request, "form": form}
            )


app = Starlette(routes=[Mount("/sqli", app=router)])


@app.on_event("startup")
async def startup():
    global pool

    pool = await asyncpg.create_pool(db_url)

    sqli_flag = os.getenv("SQLI_FLAG")

    async with pool.acquire() as con:
        await con.execute(
            """
        DROP TABLE IF EXISTS users
        """
        )
        await con.execute(
            """
        CREATE TABLE users (username TEXT NOT NULL, password TEXT NOT NULL)
        """
        )
        await con.copy_records_to_table(
            "users",
            records=[("juan", "thesniffer"), ("gnot", "agoblin"), ("admin", sqli_flag)],
        )
