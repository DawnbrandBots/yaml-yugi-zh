import os
import sys

from httpx import Client, HTTPStatusError, RequestError
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

from job import get_card_retry, wait


# Cards with a name condition https://yugipedia.com/wiki/Name_condition
passwords = [
    91932350,  # Harpie Lady 1
    27927359,  # Harpie Lady 2
    54415063,  # Harpie Lady 3
    80316585,  # Cyber Harpie Lady
    78734254,  # Neo-Spacian Marine Dolphin
    13857930,  # Neo-Spacian Twinkle Moss
    75402014,  # Ultimate Dragonic Utopia Ray
    68679595,  # Ultimate Leo Utopia Ray
    74335036,  # Fusion Substitute
    295517,  # A Legendary Ocean
    34103656,  # Lemuria, the Forgotten City
    26534688,  # Magellanica, the Deep Sea City
    2819435,  # Pacifis, the Phantasm City
]


if __name__ == "__main__":
    if sys.argv[1]:
        os.chdir(sys.argv[1])

    with Client(http2=True) as client:
        client.rate_limit = None
        yaml = YAML()
        for password in passwords:
            if os.path.exists(f"{password}.yaml"):
                print(f"{password}\tSKIP", flush=True)
                continue

            card = get_card_retry(client, password)
            if card is None:
                continue

            card["text"] = LiteralScalarString(card["text"])
            if card["pendulum"]:
                card["pendulum"] = LiteralScalarString(card["pendulum"])
            with open(f"{password}.yaml", mode="w", encoding="utf-8") as out:
                yaml.dump(card, out)
            print(f"{password}\t{client.rate_limit}", flush=True)
            wait(client)
