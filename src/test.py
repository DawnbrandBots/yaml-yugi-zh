import random
import sys
import time

from httpx import Client

from scraper import get_card


# Test cases
# passwords = [
#     10000,  # Ten Thousand Dragon
#     17390179,  # Flash Knight
#     20409757,  # Timegazer Magician
#     73779005,  # Dragoons of Draconia
#     31178212,  # Majespecter Unicorn - Kirin
#     80896940,  # Nirvana High Paladin
#     70781052,  # Summoned Skull
#     38033121,  # Dark Magician Girl
#     46986414,  # Dark Magician
#     1561110,  # ABC-Dragon Buster
#     46986415,  # N/A
# ]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        passwords = sys.argv[1:]
        with Client(http2=True) as client:
            for password in passwords:
                print(get_card(client, password))
                time.sleep(random.uniform(2, 4))
