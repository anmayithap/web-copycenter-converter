import os
from dotenv import load_dotenv
from settings import ENV_PATH

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

DEBUG = int(os.environ.get('DEBUG'))
BOT_TOKEN = str(os.getenv("TOKEN"))
ADMINS = [int(os.getenv('ADMIN'))]
RETHINK_HOST = os.getenv('HOST')
RETHINK_PORT = int(os.getenv('PORT'))
DA_TOKEN = os.getenv('DA_TOKEN')

