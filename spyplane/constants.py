import ast
import os
import sys

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
is_test = 'unittest' in sys.modules

flag_production = ast.literal_eval(os.environ.get('PRODUCTION', 'False'))

PROD_CHANNEL_BOTSPAM = 801258393205604372  # PTN bot-spam channel
PROD_CHANNEL_SCOUT = 878536094503829524
PROD_CHANNEL_MONITORING = 829215577527812096
PROD_ROLE_COUNCIL = 800091021852803072  # PTN Council role
PROD_ROLE_MOD = 813814494563401780  # PTN Mod role
PROD_ROLE_OP = 948206870491959317  # PTN Operator Role
PROD_ROLE_SCOUT = 938507320214839306  # PTN Scout Role
PROD_ROLE_SUPPORTER = 879491967157944381  # PTN Faction Supporter Role
PROD_EMOJI_TARGET = 806498760586035200  # PTN Assassin Emoji

TEST_CHANNEL_BOTSPAM = 1183552513874591845  # PANTS bot spam channel
TEST_CHANNEL_SCOUT = 878369147640234065
TEST_CHANNEL_MONITORING = 1183552554798424145
TEST_ROLE_COUNCIL = 877586918228000819  # PANTS Council role
TEST_ROLE_MOD = 903292469049974845  # PANTS Mod role
TEST_ROLE_OP = 1155985589200502844  # PANTS Operator Role
TEST_ROLE_SUPPORTER = 1182909095322341397
TEST_ROLE_SCOUT = 987800734819024977
TEST_EMOJI_TARGET = 848957573792137247

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
TOKEN = os.getenv('SPYPLANE_DISCORD_TOKEN_PROD') if flag_production else os.getenv('SPYPLANE_DISCORD_TOKEN_TESTING')
APPLICATION_ID = os.getenv('APPLICATION_ID_PROD') if flag_production else os.getenv('APPLICATION_ID_TESTING')
GUILD_ID = os.getenv('PROD_DISCORD_GUILD') if flag_production else os.getenv('TEST_DISCORD_GUILD')
CONTROL_CHANNEL = int(os.getenv('PROD_SPY_PLANE_CHANNEL_ID')) if flag_production else \
    int(os.getenv('TEST_SPY_PLANE_CHANNEL_ID'))
REPORT_CHANNEL = int(os.getenv('PROD_SPY_PLANE_REPORT_CHANNEL_ID')) if flag_production else \
    int(os.getenv('TEST_SPY_PLANE_REPORT_CHANNEL_ID'))
DB_PATH = './tests/test_workspace/spyplane.db' if is_test else './workspace/spyplane.db'

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('spyplane')

def log(msg):
    """Log an info message"""
    logger.info(msg)

def log_exception(context: str, e: Exception):
    """Log an exception with context"""
    logger.error(f"Exception in {context}: {str(e)}", exc_info=True)

# random gifs and images
error_gifs = [
    'https://media.tenor.com/-DSYvCR3HnYAAAAC/beaker-fire.gif',  # muppets
    'https://media.tenor.com/M1rOzWS3NsQAAAAC/nothingtosee-disperse.gif',  # naked gun
    'https://media.tenor.com/oSASxe-6GesAAAAC/spongebob-patrick.gif',  # spongebob
    'https://media.tenor.com/u-1jz7ttHhEAAAAC/angry-panda-rage.gif'  # panda smash
]