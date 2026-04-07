import logging
import ast
import os
import sys

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
is_test = "unittest" in sys.modules

flag_production = ast.literal_eval(os.environ.get("PRODUCTION", "False"))

PROD_CHANNEL_BOTSPAM = 801258393205604372  # PTN bot-spam channel
PROD_CHANNEL_SCOUT = 878536094503829524
PROD_CHANNEL_MONITORING = 829215577527812096
PROD_BOT_DEV_CHANNEL = 873124212406099988
PROD_GOALS_CHANNEL = 878535931580284928

PROD_ROLE_COUNCIL = 800091021852803072  # PTN Council role
PROD_ROLE_MOD = 813814494563401780  # PTN Mod role
PROD_ROLE_OP = 948206870491959317  # PTN Operator Role
PROD_ROLE_SCOUT = 938507320214839306  # PTN Scout Role
PROD_ROLE_SUPPORTER = 879491967157944381  # PTN Faction Supporter Role
PROD_EMOJI_TARGET = 806498760586035200  # PTN Assassin Emoji
PROD_EMOJI_PARTNERSHIP = 841790422698557520  # PTN Partnership Emoji
PROD_EMOJI_COURIER = 809221441915977728  # PTN Courier Emoji


TEST_CHANNEL_BOTSPAM = 1183552513874591845  # PANTS bot spam channel
TEST_CHANNEL_SCOUT = 878369147640234065 # PANTS faction scout channel
TEST_CHANNEL_MONITORING = 1183552554798424145 # PANTS bgs monitoring channel
TEST_BOT_DEV_CHANNEL = 1183552513874591845 # PANTS #spam
TEST_GOALS_CHANNEL = 1314526416238546954 # PANTS discussion channel temporarily used for goals

# Zasz server overrides. uncomment if PANTS setup is totally pants!
# TEST_CHANNEL_SCOUT = 985601752726396958 # Zasz faction scout channel
# TEST_CHANNEL_MONITORING = 985601752726396958 # Zasz bgs monitoring channel
# TEST_BOT_DEV_CHANNEL = 947026810720354347 # Zasz bot spam channel
# TEST_GOALS_CHANNEL = 976208080587091968 # Zasz goals channel

TEST_ROLE_COUNCIL = 877586918228000819  # PANTS Council role
TEST_ROLE_MOD = 903292469049974845  # PANTS Mod role
TEST_ROLE_OP = 1155985589200502844  # PANTS Operator Role
TEST_ROLE_SUPPORTER = 1182909095322341397
TEST_ROLE_SCOUT = 987800734819024977
TEST_EMOJI_TARGET = 848957573792137247
TEST_EMOJI_PARTNERSHIP = 1491078377640038440
TEST_EMOJI_COURIER = 1491078592317358120

# Environment specific vars
CHANNEL_BOTSPAM = PROD_CHANNEL_BOTSPAM if flag_production else TEST_CHANNEL_BOTSPAM
CHANNEL_SCOUT = PROD_CHANNEL_SCOUT if flag_production else TEST_CHANNEL_SCOUT
CHANNEL_MONITORING = PROD_CHANNEL_MONITORING if flag_production else TEST_CHANNEL_MONITORING
ROLE_COUNCIL = PROD_ROLE_COUNCIL if flag_production else TEST_ROLE_COUNCIL
ROLE_MOD = PROD_ROLE_MOD if flag_production else TEST_ROLE_MOD
ROLE_SUPPORTER = PROD_ROLE_SUPPORTER if flag_production else TEST_ROLE_SUPPORTER
ROLE_SCOUT = PROD_ROLE_SCOUT if flag_production else TEST_ROLE_SCOUT
ROLE_OPERATIVE = PROD_ROLE_OP if flag_production else TEST_ROLE_OP
EMOJI_ASSASSIN = PROD_EMOJI_TARGET if flag_production else TEST_EMOJI_TARGET
FACTION_SCOUT_ROLE_ID = PROD_ROLE_SCOUT if flag_production else TEST_ROLE_SCOUT
EMOJI_TARGET = PROD_EMOJI_TARGET if flag_production else TEST_EMOJI_TARGET
BOT_DEV_CHANNEL = PROD_BOT_DEV_CHANNEL if flag_production else TEST_BOT_DEV_CHANNEL
GOALS_CHANNEL = PROD_GOALS_CHANNEL if flag_production else TEST_GOALS_CHANNEL
EMOJI_PARTNERSHIP = PROD_EMOJI_PARTNERSHIP if flag_production else TEST_EMOJI_PARTNERSHIP
EMOJI_COURIER = PROD_EMOJI_COURIER if flag_production else TEST_EMOJI_COURIER

TOKEN = (
    os.getenv("SPYPLANE_DISCORD_TOKEN_PROD")
    if flag_production
    else os.getenv("SPYPLANE_DISCORD_TOKEN_TESTING")
)
APPLICATION_ID = (
    os.getenv("APPLICATION_ID_PROD")
    if flag_production
    else os.getenv("APPLICATION_ID_TESTING")
)
GUILD_ID = (
    os.getenv("PROD_DISCORD_GUILD")
    if flag_production
    else os.getenv("TEST_DISCORD_GUILD")
)
DB_PATH = "./tests/test_workspace/spyplane.db" if is_test else "./workspace/spyplane.db"

# Change to proxy URL when PTN proxy is ready
EDDN_URL = os.getenv("EDDN_URL", "tcp://eddn.edcd.io:9500")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("spyplane")


def log(msg):
    """Log an info message"""
    logger.info(msg)


def log_exception(context: str, e: Exception):
    """Log an exception with context"""
    logger.error(f"Exception in {context}: {str(e)}", exc_info=True)


# random gifs and images
hello_gifs = [
    'https://media.tenor.com/Bym53MFSVSkAAAAd/hey-hey-you-guys.gif',  # hey guys
    'https://media.tenor.com/PXiv8TqI28sAAAAC/tf2-team-fortress-2.gif',  # tf2 team fortress 2
    'https://media.tenor.com/2wftvmdVxyMAAAAC/hey-whats-up.gif',
    'https://media.tenor.com/qXf69taYAMwAAAAC/hi-mr-bean.gif',
    'https://media.tenor.com/8ga0KY2xMhAAAAAC/hafnium.gif',
    'https://media.tenor.com/xtFDWXk46GIAAAAd/tf2-spy.gif',  # tf2 spy
    'https://media.tenor.com/UYvghSt8FjMAAAAC/bond-spectre.gif',  # bond spectre
    'https://media.tenor.com/NdOG-1VFaiIAAAAC/kingsman-tux.gif',  # kingsman tux
]

error_gifs = [
    "https://media.tenor.com/-DSYvCR3HnYAAAAC/beaker-fire.gif",  # muppets
    "https://media.tenor.com/M1rOzWS3NsQAAAAC/nothingtosee-disperse.gif",  # naked gun
    "https://media.tenor.com/oSASxe-6GesAAAAC/spongebob-patrick.gif",  # spongebob
    "https://media.tenor.com/u-1jz7ttHhEAAAAC/angry-panda-rage.gif",  # panda smash
    "https://media.tenor.com/kgsVoZcNACsAAAAC/not-my-problem-dont-care-didnt-ask.gif",
    "https://media.tenor.com/jJl0gYeP-8QAAAAd/johnny-english-rowan-atkinson.gif"
]
