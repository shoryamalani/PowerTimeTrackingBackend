import dotenv
import os
dotenv.load_dotenv()
APPLE_NOTIFICATION_TOKEN = os.environ.get('APPLE_NOTIFICATION_TOKEN')
TEAM_ID = os.environ.get('TEAM_ID')
AUTH_FILE_PATH = os.environ.get('AUTH_FILE_PATH')
APPLE_PASSPHRASE_NOTIFICATIONS = os.environ.get('NOTIFICATION_PASSWORD')
CERT_FILE_PATH = os.environ.get('CERT_FILE_PATH')