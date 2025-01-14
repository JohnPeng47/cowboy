import functools
import random
import string
import uuid
import time
import functools
import git
import configparser
from pathlib import Path
from colorama import Fore, Style
from pathlib import Path
from typing import List, Set

from src.logger import testgen_logger


# support for all strings as multi-line
import yaml

def str_presenter(dumper, data):
    """Configure yaml for dumping multiline strings."""
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data.strip(), style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)


# nested level get() function
def resolve_attr(obj, attr, default=None):
    """Attempts to access attr via dotted notation, returns none if attr does not exist."""
    try:
        return functools.reduce(getattr, attr.split("."), obj)
    except AttributeError:
        return default


def gen_random_name():
    """
    Generates a random name using ASCII, 8 characters in length
    """

    return "".join(random.choices(string.ascii_lowercase, k=8))


def generate_id():
    """
    Generates a random UUID
    """
    return str(uuid.uuid4())


def async_timed(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        testgen_logger.info(
            f"Function {func.__name__} took {end_time - start_time:.4f} seconds"
        )
        return result

    return wrapper

def confirm_action(prompt: str) -> bool:
    """Get user confirmation for an action"""
    while True:
        response = input(f"{prompt}\nDo you want to apply the patch (y/N): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no', '']:
            return False
        print("Please answer 'y' or 'n'")

def sync_timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(
            f"Function {func.__name__} took {end_time - start_time:.4f} seconds"
        )
        return result

    return wrapper

def get_repo_head(repo_path: Path):
    """Returns the head commit hash of a git repository"""
    return git.Repo(repo_path).head.commit.hexsha

def cyan_text(text: str) -> str:
    """Returns text in red color using colorama"""
    return f"{Fore.CYAN}{text}{Style.RESET_ALL}"
    
def green_text(text: str) -> str:
    """Returns text in green color using colorama"""
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"

def red_text(text: str) -> str:
    """Returns text in red color using colorama"""
    return f"{Fore.RED}{text}{Style.RESET_ALL}"

def dim_text(text: str) -> str:
    """Returns text in dim color using colorama"""
    return f"{Style.DIM}{text}{Style.RESET_ALL}"
