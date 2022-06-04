import random
import sqlite3
import sys
import time

from httpx import Client
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

from scraper import get_card


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
            card = get_card(client, password)._asdict()
            card["text"] = LiteralScalarString(card["text"])
            if card["pendulum"]:
                card["pendulum"] = LiteralScalarString(card["text"])
            with open(f"{password}.yaml", mode="w", encoding="utf-8") as out:
                yaml.dump(card, out)
            print(password)
            time.sleep(random.uniform(2, 4))
