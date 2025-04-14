import os
from dotenv import load_dotenv
from logging import getLogger, StreamHandler

logger = getLogger(__name__)
logger.setLevel("INFO")
logger.addHandler(StreamHandler())
logger.info("Loading environment variables")

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
RAPID_API_HOST = os.getenv("RAPID_API_HOST")
RAPID_API_URL = os.getenv("RAPID_API_URL")
