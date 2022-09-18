# SPDX-FileCopyrightText: © 2022 Kevin Lu
# SPDX-Licence-Identifier: LGPL-3.0-or-later
from typing import NamedTuple, Optional

from bs4 import BeautifulSoup
import httpx


class CardText(NamedTuple):
    name: str
    text: str
    pendulum: Optional[str]


def strip_text(raw: str) -> str:
    # Remove prefixed labels that are inconsistently applied. There may be additional prefixes to these, separated by ·,
    # but we only need to match the last characters before the colon rather than every combination of labels
    # Maybe 效果· *** could be matched?
    prefixes = [
        "描述：",  # Flavour text
        "效果：",  # Effect, usually on Pendulums
        "灵摆：",  # Pendulum
        "特殊召唤：",  # Special Summon (e.g. Eater of Millions)
        "调整：",  # Tuner
        "卡通：",  # Toon
        "灵魂：",  # Spirit
        "同盟：",  # Union
        "二重：",  # Gemini
        "效果·反转：",  # Flip, but not "FLIP:"
        "融合：",  # Fusion
        "同调：",  # Synchro
        "XYZ：",
        "连接：",  # Link
    ]
    for prefix in prefixes:
        raw = raw.split(prefix, maxsplit=1)[-1]
    return raw


def get_card(client: httpx.Client, *, password: Optional[int] = None, slug: Optional[str] = None) -> Optional[CardText]:
    """
    Parses card text from the website. HTTP errors are raised. Rate limits are recorded in client.rate_limit

    :param client: HTTPX Client. May support HTTP2 but shouldn't have defaults that majorly change behaviour.
    :param password: Card password to fetch.
    :param slug: Direct slug of the page to fetch, alternatively.
    :return: None if card not found, otherwise a NamedTuple of the result.
    """
    if password is not None:
        url = f"https://www.ourocg.cn/search/{password}"
    elif slug is not None:
        url = f"https://www.ourocg.cn/card/{slug}"
    else:
        raise ValueError("Must provide one of password or slug")
    response = client.get(url, follow_redirects=True)
    try:
        client.rate_limit = int(response.headers.get("x-ratelimit-remaining"))
    except:
        client.rate_limit = None
    response.raise_for_status()
    if password is not None and response.url == url:  # Must be redirected for the search to have a match
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    name = soup.h1.div.text.strip()  # Could use .string

    text_span = soup.find("div", attrs={"class": "effect"}).span
    if text_span.div:  # class="line" separating Pendulum and main text
        stripped_strings = tuple(text_span.stripped_strings)
        if "灵摆效果：" in stripped_strings[0]:  # default case, Pendulum text comes first
            pendulum, *text = stripped_strings
        elif "灵摆效果：" in stripped_strings[-1]:  # uncommon ill-formatted case, Pendulum text comes second
            *text, pendulum = stripped_strings
        else:  # indeterminate case, so far only known to occur with 47075569 Performapal Pendulum Sorcerer
            return None
        pendulum = pendulum.split("灵摆效果：")[1]  # Remove prefixed label
        if pendulum == "无":
            pendulum = None
        text = "\n".join(text)  # Sometimes a <br /> separates the main card text when there's a Material line
    else:
        pendulum = None
        text = "\n".join(text_span.stripped_strings)  # Could use .text.strip()
    text = strip_text(text)
    return CardText(name, text, pendulum)
