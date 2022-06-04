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
        "特殊召唤：",  # Special Summon (e.g. Eater of Millions)
        "调整：",  # Tuner
        "卡通：",  # Toon
        "灵魂：",  # Spirit
        "同盟：",  # Union
        "二重：",  # Gemini
        "反转：",  # Flip
        "融合：",  # Fusion
        "同调：",  # Synchro
        "XYZ：",
        "连接：",  # Link
    ]
    for prefix in prefixes:
        raw = raw.split(prefix, maxsplit=1)[-1]
    return raw


def get_card(client: httpx.Client, password: int) -> Optional[CardText]:
    url = f"https://www.ourocg.cn/search/{password}"
    response = client.get(url, follow_redirects=True)
    # print(response.request.headers)
    # print(response.headers)
    # print(response.headers.get("x-ratelimit-remaining"))
    response.raise_for_status()
    if response.url == url:  # Must be redirected for the search to have a match
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    name = soup.h1.div.text.strip()  # Could use .string

    text_span = soup.find("div", attrs={"class": "effect"}).span
    if text_span.div:  # class="line" separating Pendulum and main text
        pendulum, *text = text_span.stripped_strings
        pendulum = pendulum.split("灵摆效果：")[1]  # Remove prefixed label
        # 无
        text = "\n".join(text)  # Sometimes a <br /> separates the main card text when there's a Material line
    else:
        pendulum = None
        text = "\n".join(text_span.stripped_strings)  # Could use .text.strip()
    text = strip_text(text)
    return CardText(name, text, pendulum)
