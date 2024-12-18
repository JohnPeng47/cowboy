from starlette.config import Config
from enum import Enum
from pathlib import Path

config = Config(".env")

ENV = config("ENV", default="dev")
PORT = config("PORT")
API_ENDPOINT = "http://18.223.150.134:" + PORT

# JWT settings
COWBOY_JWT_SECRET = config("DISPATCH_JWT_SECRET", default="")
COWBOY_JWT_ALG = config("DISPATCH_JWT_ALG", default="HS256")
COWBOY_JWT_EXP = config("DISPATCH_JWT_EXP", cast=int, default=308790000)  # Seconds

COWBOY_OPENAI_API_KEY = config("OPENAI_API_KEY")

DB_PASS = config("DB_PASS")
DB_NAME = config("DB_NAME")
DB_USER = config("DB_USER")
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{DB_USER}:{DB_PASS}@127.0.0.1:5432/{DB_NAME}"
)
SQLALCHEMY_ENGINE_POOL_SIZE = 50

ALEMBIC_INI_PATH = "."
ALEMBIC_CORE_REVISION_PATH = "alembic"

# LLM settings and test gen settings
AUGMENT_ROUNDS = 3 if ENV == "release" else 1
LLM_RETRIES = 3
AUTO_GEN_SIZE = 7
MAX_CTXT_SIZE = 10000

# Run test settings 
RUN_TEST = "app"
TESTCONFIG_ROOT = Path("src/eval/configs")

LOG_DIR = "log"
REPOS_ROOT = "repos"
AWS_REGION = "us-east-2"

# braintrust settingss
BT_PROJECT = "Cowboy"
BRAINTRUST_API_KEY = config("BRAINTRUST_API_KEY")

EVAL_DATA_ROOT = Path("src/eval/datasets")
EVAL_OUTPUT_ROOT = Path("src/eval/output")

class Language(str, Enum):
    """
    Currently supported languages
    """
    python = "python"
