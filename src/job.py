import random
import sqlite3
import sys
import time

from httpx import Client, HTTPStatusError
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

from scraper import get_card


def wait(client: Client) -> None:
    """
    Uses a custom attribute set by get_card to sleep for longer if needed.
    """
    if client.rate_limit and client.rate_limit < 10:
        time.sleep(random.uniform(10, 20))
    else:
        time.sleep(random.uniform(2, 4))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(f"Usage: {sys.argv[0]} <cards.cdb> <partition size> <partition index>")

    file = sys.argv[1]
    size = int(sys.argv[2])
    index = int(sys.argv[3])
    with sqlite3.connect(file) as connection:
        cursor = connection.cursor()
        cursor: sqlite3.Cursor
        cursor.execute(
            "SELECT id FROM datas WHERE alias = 0 LIMIT ? OFFSET ?",
            (size, index * size)
        )
        cards = cursor.fetchall()
        cursor.close()
        del cursor

    with Client(http2=True) as client:
        yaml = YAML()
        for (password,) in cards:
            try:
                card = get_card(client, password)._asdict()
            except HTTPStatusError as e:
                print(f"{password}\t{client.rate_limit}\tFAIL {e.response.status_code}", flush=True)
                wait(client)
                continue

            card["text"] = LiteralScalarString(card["text"])
            if card["pendulum"]:
                card["pendulum"] = LiteralScalarString(card["text"])
            with open(f"{password}.yaml", mode="w", encoding="utf-8") as out:
                yaml.dump(card, out)
            print(f"{password}\t{client.rate_limit}", flush=True)
            wait(client)
