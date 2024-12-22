import pytest
import git
import json

from cowboy_lib.repo import SourceRepo
from src.local.db import get_repo
from src.repo.models import RepoConfig
from src.config import TESTCONFIG_ROOT

pytest_plugins = ['pytest_asyncio']


git_commit = "57cc0790facddab289dae9c78afbdf814b692d64"

@pytest.fixture
def test_repoconfig():
    return get_repo("testrepo", ret_json=False)

@pytest.fixture
def source_repo(test_repoconfig):
    print(test_repoconfig)
    git_repo = git.Repo(test_repoconfig.source_folder)
    git_repo.git.checkout(git_commit, force=True)
    git_repo.git.reset("--hard", git_commit)

    yield SourceRepo(test_repoconfig.source_folder)