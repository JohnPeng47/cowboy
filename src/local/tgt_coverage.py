from cowboy_lib.coverage import TestCoverage
from cowboy_lib.repo import SourceRepo
from cowboy_lib.test_modules import TestModule

from src.tasks.get_baseline_parallel import get_tm_target_coverage
from src.runner.local.run_test import run_test as run_test_local

async def enrich_tm_with_tgt_coverage(repo_name: str, 
                              src_repo: SourceRepo, 
                              base_cov: TestCoverage,
                              test_module: TestModule):
    """
    Collects chunks of code executed by the TestModule
    """
    chunks = await get_tm_target_coverage(
        repo_name=repo_name,
        src_repo=src_repo,
        tm=test_module,
        base_cov=base_cov,
        run_test=run_test_local,
        run_args=None
    )
    return chunks