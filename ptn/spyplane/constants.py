import os
import sys
from pathlib import Path

from ptn_utils.global_constants import DATA_DIR

is_test = "unittest" in sys.modules

DATA_DIR_PATH = Path(DATA_DIR)

DB_PATH = "./tests/test_workspace/spyplane.db" if is_test else str(DATA_DIR_PATH / "spyplane.db")

EDDN_URL = os.getenv("EDDN_URL", "tcp://eddn.edcd.io:9500")


hello_gifs = [
    "https://media.tenor.com/Bym53MFSVSkAAAAd/hey-hey-you-guys.gif",  # hey guys
    "https://media.tenor.com/PXiv8TqI28sAAAAC/tf2-team-fortress-2.gif",  # tf2 team fortress 2
    "https://media.tenor.com/2wftvmdVxyMAAAAC/hey-whats-up.gif",
    "https://media.tenor.com/qXf69taYAMwAAAAC/hi-mr-bean.gif",
    "https://media.tenor.com/8ga0KY2xMhAAAAAC/hafnium.gif",
    "https://media.tenor.com/xtFDWXk46GIAAAAd/tf2-spy.gif",  # tf2 spy
    "https://media.tenor.com/UYvghSt8FjMAAAAC/bond-spectre.gif",  # bond spectre
    "https://media.tenor.com/NdOG-1VFaiIAAAAC/kingsman-tux.gif",  # kingsman tux
]

error_gifs = [
    "https://media.tenor.com/-DSYvCR3HnYAAAAC/beaker-fire.gif",  # muppets
    "https://media.tenor.com/M1rOzWS3NsQAAAAC/nothingtosee-disperse.gif",  # naked gun
    "https://media.tenor.com/oSASxe-6GesAAAAC/spongebob-patrick.gif",  # spongebob
    "https://media.tenor.com/u-1jz7ttHhEAAAAC/angry-panda-rage.gif",  # panda smash
    "https://media.tenor.com/kgsVoZcNACsAAAAC/not-my-problem-dont-care-didnt-ask.gif",
    "https://media.tenor.com/jJl0gYeP-8QAAAAd/johnny-english-rowan-atkinson.gif",
]
