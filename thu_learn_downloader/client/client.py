from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Optional, Union
from pathlib import Path
import json

from requests import Response, Session
from requests.cookies import create_cookie

MAX_SIZE: int = 200

class Language(StrEnum):
    ENGLISH = "en"
    CHINESE = "zh"


class Client(Session):
    language: Language

    def __init__(self, language: Language = Language.ENGLISH, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.language = language

    def get_with_token(
        self, url: str, params: Optional[Mapping[str, Any]] = None
    ) -> Response:
        params = params or {}
        return self.get(url=url, params={**params, "_csrf": self.token})

    @property
    def token(self) -> None:
        return self.cookies["XSRF-TOKEN"]

    def save_cookies(self, filepath: Union[str, Path]) -> None:
        cookies_dict = []
        for cookie in self.cookies:
            cookies_dict.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "expires": cookie.expires,
                "rest": cookie._rest,  # Optional extras
            })
        Path(filepath).write_text(json.dumps(cookies_dict, indent=2), encoding="utf-8")

    def load_cookies(self, filepath: Union[str, Path]) -> None:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Cookie file not found: {filepath}")

        cookies_dict = json.loads(filepath.read_text(encoding="utf-8"))
        for c in cookies_dict:
            cookie = create_cookie(
                name=c["name"],
                value=c["value"],
                domain=c["domain"],
                path=c["path"],
                secure=c["secure"],
                expires=c["expires"],
                rest=c.get("rest", {})
            )
            self.cookies.set_cookie(cookie)