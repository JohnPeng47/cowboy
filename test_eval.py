from src.runner.local.run_test import get_repo_config
import asyncio
from pathlib import Path
from src.tasks.get_baseline_parallel import get_tm_target_coverage
from src.test_modules.iter_tms import iter_test_modules
from cowboy_lib.repo.source_repo import SourceRepo
from cowboy_lib.test_modules.test_module import TestModule
from cowboy_lib.coverage import TestCoverage
from src.runner.service import RunServiceArgs
from src.queue.core import TaskQueue
from src.runner.local.run_test import run_test

async def test_get_coverage():
    repo_name = "textual-neutered"
    repo_config = get_repo_config(repo_name)
    repo_path = Path(repo_config.source_folder)
    src_repo = SourceRepo(repo_path)
    # tm = iter_test_modules(src_repo, lambda tm: tm.name == "TestWoodpecker")

    base_cov = await run_test(repo_name, None)

    print(base_cov.get_coverage())

    # base_cov = TestCoverage([])
        
    # chunks = await get_tm_target_coverage(
    #     repo_name=repo_name,
    #     src_repo=src_repo,
    #     tm=tm,
    #     base_cov=base_cov,
    #     run_test=run_test,
    #     run_args=None
    # )
    
    # return chunks

if __name__ == "__main__":
    asyncio.run(test_get_coverage())