import functools
import re
import typer
from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import sync_playwright
from requests import Response
from requests.cookies import RequestsCookieJar
from gmssl import sm2

from thu_learn_downloader.common.typing import cast
from . import url
from .client import Client, Language
from .semester import Semester

class Learn:
    client: Client

    def __init__(self, language: Language = Language.ENGLISH, *args, **kwargs) -> None:
        self.client = Client(language, *args, **kwargs)

    def login(self, username: str, password: str) -> None:
        response: Response = self.client.get(url=url.make_url(), verify=False)
        soup: BeautifulSoup = BeautifulSoup(
            markup=response.text, features="html.parser"
        )
        login_button: Tag = cast(Tag, soup.select_one(selector="#loginButtonId"))
        onclick: str = cast(str, login_button["onclick"])
        login_url: str = cast(str, re.search(r"'(https?://[^']+)'", onclick).group(1))

        soup: BeautifulSoup = BeautifulSoup(
            markup=self.client.get(url=login_url).text, features="html.parser"
        )

        soup: BeautifulSoup = BeautifulSoup(
            markup=self.client.get(url="https://id.tsinghua.edu.cn/do/off/ui/auth/login/form/bb5df85216504820be7bba2b0ae1535b/0").text, features="html.parser"
        )
        sm2pubkey = soup.select_one(selector="#sm2publicKey").text.strip()
        sm2_encryptor = sm2.CryptSM2(public_key=sm2pubkey, private_key=None, mode=1)
        response = self.client.post(url="https://id.tsinghua.edu.cn/do/off/ui/auth/login/check", data={"i_user":username, "i_pass": '04'+sm2_encryptor.encrypt(password).hex()})

        if "<title>二次认证</title>" in response.text or "doubleAuth.bundle.js" in response.text:
            typer.echo("Username and password verified. Proceeding to the next step.")
            # Here you would add the logic to handle the 2FA page.
            # For now, we confirm success and return True.
            return True
        else:
            return False

        status = query.get("status", ["unknown"])[0]
        ticket = query.get("ticket", [None])[0]
        if ticket is None:
            print("Login probably failed — no ticket received.")
            print("Full query dict:", query)
            return

        self.client.get(url=href, verify=False)
        self.client.get(
            url=url.make_url(path="/b/j_spring_security_thauth_roaming_entry"),
            params={"ticket": ticket},
            verify = False
        )
        self.client.get(url=url.make_url(path="/f/wlxt/index/course/student/"), verify=False)
        assert status == "SUCCESS"

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

