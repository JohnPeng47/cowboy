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


def get_repo_config(repo_name: str) -> RepoConfig:
    with open(Path(TESTCONFIG_ROOT) / f"{repo_name}.json", "r") as f:
        return RepoConfig(**json.load(f))   


@cache_test_run
async def run_test(
    repo_name: str,
    service_args: RunServiceArgs, # dont actually need this argument here, just for compatability
    exclude_tests: List[Tuple[Function, str]] = [],
    include_tests: List[str] = [],
    patch_file: PatchFile = None,
    stream: bool = False,
) -> CoverageResult:
    print("wtf??")
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