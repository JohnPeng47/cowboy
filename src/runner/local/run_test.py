from cowboy_lib.repo.repository import PatchFile
from cowboy_lib.api.runner.shared import RunTestTaskArgs
from cowboy_lib.coverage import CoverageResult
from cowboy_lib.ast.code import Function

from ..models import RunServiceArgs 
from .python import PytestDiffRunner
from .models import RepoConfig
from .cache import cache_test_run

from src.config import TESTCONFIG_ROOT
from pathlib import Path
from typing import List, Tuple
import json

class RepoConfigException(Exception):
    pass


def get_repo_config(repo_name: str, ret_json = False) -> RepoConfig:
    filename = f"{repo_name}.json"
    with open(TESTCONFIG_ROOT / filename, "r") as f:
        if ret_json:
            return json.load(f)
        
        config = RepoConfig(**json.load(f))
        if config.repo_name != repo_name:
            raise RepoConfigException(f"Config.repo_name must be the same as the filename {filename}")
    
        return config

@cache_test_run
async def run_test(
    repo_name: str,
    service_args: RunServiceArgs, # dont actually need this argument here, just for compatability
    exclude_tests: List[Tuple[Function, str]] = [],
    include_tests: List[str] = [],
    patch_file: PatchFile = None,
    stream: bool = False,
    use_cache: bool = True,
    delete_last: bool = False
) -> CoverageResult:
    repo_config = get_repo_config(repo_name)
    args = RunTestTaskArgs(
        repo_name=repo_name,
        patch_file=patch_file,
        exclude_tests=exclude_tests,
        include_tests=include_tests,
    )
    runner = PytestDiffRunner(repo_config)
    cov, _, _ = runner.run_testsuite(args, stream=stream)

    return cov