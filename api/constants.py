import dotenv
import os
dotenv.load_dotenv()
APPLE_NOTIFICATION_TOKEN = os.environ.get('APPLE_NOTIFICATION_TOKEN')
CREDS_FILE_PATH = os.environ.get('CREDS_FILE_PATH')
TEAM_ID = os.environ.get('TEAM_ID')
AUTH_FILE_PATH = os.environ.get('AUTH_FILE_PATH')