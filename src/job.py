# SPDX-FileCopyrightText: © 2022 Kevin Lu
# SPDX-Licence-Identifier: LGPL-3.0-or-later
from argparse import ArgumentParser
import json
import os
import random
import sqlite3
import time
from typing import Any, Dict, Optional

from httpx import Client, HTTPStatusError, RequestError
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

from scraper import get_card


parser = ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--cdb", help="CDB containing passwords to scrape")
group.add_argument("--json", help="YAML Yugi aggregate JSON containing passwords to scrape")
parser.add_argument("--size", type=int, required=True, help="Partition size per worker process")
parser.add_argument("--index", type=int, required=True, help="Partition index for this worker process")
parser.add_argument("--output", help="Optional output directory")
parser.add_argument("--skip", action="store_true", help="Skip already-existing files")


def wait(client: Client, retry: int = 0) -> None:
    """
    Uses a custom attribute set by get_card to sleep for longer if needed.
    """
    if client.rate_limit and client.rate_limit < 10:
        time.sleep(random.uniform(20, 30))
    else:
        time.sleep(random.uniform(2 + retry, 4 + retry))


def get_card_retry(*args, **kwargs) -> Optional[Dict[str, Any]]:
    for retry in range(5):
        try:
            card = get_card(*args, **kwargs)
            if card:
                return card._asdict()
            else:
                print(f"{password}\t{client.rate_limit}\tNOT FOUND", flush=True)
                wait(client)
                return
        except HTTPStatusError as e:
            print(f"{password}\t{client.rate_limit}\tFAIL {e.response.status_code}", flush=True)
            wait(client)
            return
        except RequestError as e:
            print(f"{password}\tTRY {retry}\t{e}", flush=True)
            wait(client, retry)


OVERRIDES = {
    10000000: "0zsP0",  # Obelisk
    10000010: "nJsMA",  # Ra
    10000020: "o0sgV",  # Osiris
    10000030: "lNs5nA",  # Magi Magi
    10000040: "lNs5o7",  # Holactie
    10000080: "rks4pk",  # Sphere
    10000090: "PPsX1b",  # Phoenix
}

if __name__ == "__main__":
    args = parser.parse_args()
    if args.cdb:
        with sqlite3.connect(args.cdb) as connection:
            cursor = connection.cursor()
            cursor: sqlite3.Cursor
            cursor.execute(
                "SELECT id FROM datas WHERE alias = 0 AND (type & 0x4000 = 0) LIMIT ? OFFSET ?",
                # "SELECT id FROM datas WHERE alias = 0 AND type & 0x1000000 ORDER BY id DESC LIMIT ? OFFSET ?",
                (args.size, args.index * args.size)
            )
            cards = cursor.fetchall()
            cards = [password for (password,) in cards]
            cursor.close()
            del cursor
    else:
        with open(args.json) as handle:
            data = json.load(handle)
        print(f"Found {len(data)} cards.", flush=True)
        cards = [card["password"] for card in data if card.get("password")]
        print(f"Considering {len(cards)} cards with passwords.", flush=True)
        cards = cards[args.index * args.size:(args.index + 1) * args.size]

    if args.output:
        os.chdir(args.output)

    with Client(http2=True) as client:
        client.rate_limit = None
        yaml = YAML()
        for password in cards:
            if args.skip and os.path.exists(f"{password}.yaml"):
                # print(f"{password}\tSKIP", flush=True)
                continue

            if password not in OVERRIDES:
                card = get_card_retry(client, password=password)
            else:
                card = get_card_retry(client, slug=OVERRIDES[password])
            if card is None:
                continue

            card["text"] = LiteralScalarString(card["text"])
            if card["pendulum"]:
                card["pendulum"] = LiteralScalarString(card["pendulum"])
            else:
                card.pop("pendulum")
            with open(f"{password}.yaml", mode="w", encoding="utf-8") as out:
                yaml.dump(card, out)
            print(f"{password}\t{client.rate_limit}", flush=True)
            wait(client)
