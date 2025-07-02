import functools
import re
import urllib.parse
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import ParseResult

import typer
from bs4 import BeautifulSoup, Tag
from gmssl import sm2
from requests import Response

from thu_learn_downloader.common.typing import cast
from . import url
from .client import Client, Language
from .semester import Semester

cookie_path = Path.home() / ".thu-learn-downloader_cookies.json"

class Learn:
    client: Client

    def __init__(self, language: Language = Language.ENGLISH, *args, **kwargs) -> None:
        self.client = Client(language, *args, **kwargs)

    def is_logged_in(self) -> bool:
        try:
            r = self.client.get_with_token(
            url=url.make_url(path="/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq")
        )  # example: user profile
            return r.status_code == 200 and "失效" in r.text
        except Exception:
            return False

    def login_stage1(self, username: str, password: str):
        response: Response = self.client.get(url=url.make_url(), verify=False)
        soup: BeautifulSoup = BeautifulSoup(
            markup=response.text, features="html.parser"
        )
        login_button: Tag = cast(Tag, soup.select_one(selector="#loginButtonId"))
        onclick: str = cast(str, login_button["onclick"])
        login_url: str = cast(str, re.search(r"'(https?://[^']+)'", onclick).group(1))

        BeautifulSoup(
            markup=self.client.get(url=login_url).text, features="html.parser"
        )

        soup: BeautifulSoup = BeautifulSoup(
            markup=self.client.get(url="https://id.tsinghua.edu.cn/do/off/ui/auth/login/form/bb5df85216504820be7bba2b0ae1535b/0").text, features="html.parser"
        )
        sm2pubkey = soup.select_one(selector="#sm2publicKey").text.strip()
        sm2_encryptor = sm2.CryptSM2(public_key=sm2pubkey, private_key=None, mode=1)
        response = self.client.post(url="https://id.tsinghua.edu.cn/do/off/ui/auth/login/check", data={"i_user": username, "i_pass": '04'+sm2_encryptor.encrypt(password.encode('utf-8')).hex()})

        if "<title>二次认证</title>" in response.text or "doubleAuth.bundle.js" in response.text:
            typer.echo("Username and password verified. Proceeding to the next step.")
            # Here you would add the logic to handle the 2FA page.
            # For now, we confirm success and return True.
            return True
        else:
            return False

    def login_stage2(self):
        response: Response = self.client.post(url="https://id.tsinghua.edu.cn/b/doubleAuth/login", data={"action": "FIND_APPROACHES"})
        data = response.json()

        if data.get("result") != "success":
            print("Failed to retrieve authentication methods.")
            print("Response data:", data)
            return None

        methods = []
        auth_object = data.get("object", {})

        if auth_object.get("hasWeChatBool"):
            methods.append("WeChat")

        if auth_object.get("phone"):
            methods.append(f"Mobile {auth_object['phone']}")

        if not methods:
            print("No authentication methods available.")
            return None

        selected_method = ""
        if len(methods) == 1:
            selected_method = methods[0].split(" ")[0].lower()
            typer.echo(f"Automatically selected the only available 2FA option: {methods[0]}")
        else:
            while True:
                typer.echo("Please select a 2FA method:")
                for i, method in enumerate(methods, start=1):
                    typer.echo(f"{i}. {method}")

                try:
                    selection = typer.prompt("Enter the number of your choice", type=int)
                    if 1 <= selection <= len(methods):
                        selected_method = methods[selection - 1].split(" ")[0].lower()
                        break
                    else:
                        # If number is out of range, print error and loop again
                        typer.secho("Invalid selection. Please enter a number from the list.", fg=typer.colors.RED)
                except typer.Abort:
                    # Handle Ctrl+C
                    typer.secho("\nSelection cancelled.", fg=typer.colors.YELLOW)
                    raise
                except ValueError:
                    # Handle non-integer input
                    typer.secho("Invalid input. Please enter a number.", fg=typer.colors.RED)
        response: Response = self.client.post(
            url="https://id.tsinghua.edu.cn/b/doubleAuth/login",
            data={"action": "SEND_CODE", "type": selected_method}
        )

        if response.json().get("result") != "success":
            print("Failed to send the authentication code.")
            print("Response data:", response.json())
            return None
        typer.echo(f"Authentication code sent via {selected_method}. Please check your device.")

        while True:
            code = typer.prompt("Enter the authentication code")
            response: Response = self.client.post(
                url="https://id.tsinghua.edu.cn/b/doubleAuth/login",
                data={"action": "VERITY_CODE", "vericode": code}
            )
            response_json = response.json()

            if response_json.get("result") == "success":
                redirect_url = response_json.get("object", {}).get("redirectUrl", "")
                typer.echo("Authentication successful.")
                break
            else:
                typer.secho(response_json.get("msg"), fg=typer.colors.RED)
                if "失效" in response_json.get("msg"):
                    typer.echo("Code has expired, sending a new code.")
                    self.client.post(
                        url="https://id.tsinghua.edu.cn/b/doubleAuth/login",
                        data={"action": "SEND_CODE", "type": selected_method}
                    )

        response: Response = self.client.get(url="https://id.tsinghua.edu.cn" + redirect_url)
        soup: BeautifulSoup = BeautifulSoup(
            markup=response.text, features="html.parser"
        )
        a: Tag = cast(Tag, soup.select_one(selector="a"))
        href: str = cast(str, a["href"])
        parse_result: ParseResult = urllib.parse.urlparse(url=href)
        query: dict[str, list[str]] = urllib.parse.parse_qs(qs=parse_result.query)
        print("Query received:", query)

        ticket = query.get("ticket", [None])[0]
        if ticket is None:
            print("Login probably failed — no ticket received.")
            print("Full query dict:", query)
            return None

        self.client.get(url=href, verify=False)
        self.client.save_cookies(cookie_path)
        return True

    @functools.cached_property
    # def semesters(self) -> Sequence[Semester]:
    #     return [
    #         Semester(client=self.client, id=result)
    #         for result in self.client.get_with_token(
    #             url=url.make_url(path="/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq")
    #         ).json()
    #     ]
    def semesters(self) -> Sequence[Semester]:
        response = self.client.get_with_token(
            url=url.make_url(path="/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq")
        )

        if response.status_code != 200:
            print("Request failed with status:", response.status_code)
            return []

        print(response.text)

        try:
            data = response.json()
            print("Parsed JSON:", data)  # Debugging output

            # Filter out None values
            filtered_data = [item for item in data if item is not None]
        except Exception as e:
            print("JSON decoding error:", e)
            return []

        return [Semester(client=self.client, id=result) for result in filtered_data]

