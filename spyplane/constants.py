import ast
import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

flag_production = ast.literal_eval(os.environ.get('PRODUCTION', 'False'))

# Common environment variables
GDRIVE_TOKEN = os.path.join(os.getcwd(), 'workspace/token.json') if "/tests" not in os.getcwd() else os.path.join(os.getcwd(), '../token.json')  # CWD = /tests/ for tests
BGS_BOT_USER_ID = int(os.getenv('BGS_BOT_USER_ID'))

# Environment specific vars
FACTION_SCOUT_ROLE_ID = 938507320214839306 if flag_production else 976913675355037716  # PTN MAIN or PTN TEST  @Faction-Scout: 987800734819024977
EMOJI_BULLSEYE = 848957573792137247 # PTN MAIN :assasin: PTN test server :assassin:
TOKEN = os.getenv('SPYPLANE_DISCORD_TOKEN_PROD') if flag_production else os.getenv('SPYPLANE_DISCORD_TOKEN_TESTING')
APPLICATION_ID = os.getenv('APPLICATION_ID_PROD') if flag_production else os.getenv('APPLICATION_ID_TESTING')
GUILD_ID = os.getenv('PROD_DISCORD_GUILD') if flag_production else os.getenv('TEST_DISCORD_GUILD')
CONTROL_CHANNEL = int(os.getenv('PROD_SPY_PLANE_CHANNEL_ID')) if flag_production else \
    int(os.getenv('TEST_SPY_PLANE_CHANNEL_ID'))
REPORT_CHANNEL = int(os.getenv('PROD_SPY_PLANE_REPORT_CHANNEL_ID')) if flag_production else \
    int(os.getenv('TEST_SPY_PLANE_REPORT_CHANNEL_ID'))
TICK_CHANNEL = int(os.getenv('PROD_TICK_DETECTION_CHANNEL_ID')) if flag_production else \
    int(os.getenv('TEST_TICK_DETECTION_CHANNEL_ID'))
DB_PATH = './test_workspace/spyplane.db' if 'tests' in os.getcwd() else './workspace/spyplane.db'

def log(msg):
    print(msg, flush=True)

def log_exception(context: str, e: Exception):
    log(f"Exception in {context}")
    log(str(e)) # e can be logged only after conversion into a string
