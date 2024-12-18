import json
from typing import List, Optional, Dict
from pathlib import Path
from collections import defaultdict
from sqlalchemy.orm import Session, sessionmaker
from braintrust import init_dataset, Dataset

from cowboy_lib.coverage import TestCoverage
from cowboy_lib.repo import SourceRepo
from cowboy_lib.test_modules import TestModule
from cowboy_lib.ast import NodeType

from src.tasks.get_baseline_parallel import get_tm_target_coverage
from src.config import REPOS_ROOT, BRAINTRUST_API_KEY, BT_PROJECT, TESTCONFIG_ROOT
from src.test_modules.iter_tms import iter_test_modules
from src.database.core import engine
from src.runner.local.run_test import run_test as run_test_local
from src.local.db import get_repo
from src.local.models import TestModuleEvalData
from src.logger import buildtm_logger as log

class NoTestsToDelete(Exception):
    pass

# Create a session factory (similar to main.py)
Session = sessionmaker(bind=engine)

def num_delete(tm: TestModule, to_keep: int = 1, to_delete: int = 1) -> int:
    if to_keep and to_delete:
        raise Exception("Cannot have both values > 0")

    # always leave at least one test
    if to_keep:
        num_to_del = max(0, len(tm.tests) - to_keep)
        return num_to_del
    elif to_delete:
        num_to_del = min(len(tm.tests) - 1, to_delete)
        return num_to_del
    else:
        raise Exception("Must provide either to_keep or to_delete value")

async def neuter_repo(
    dataset: Dataset,
    repo_name: str,
    test_modules: List[TestModule], 
    src_repo: SourceRepo, 
    base_cov: TestCoverage,
    to_keep, 
    to_delete=0,
    max_tm=None,
    out_repo: Optional[Path] = None
):
    """
    Iterate TestModules and delete tests from each according to to_keep/to_delete. 
    Process up to max_tm test modules. Writes summary of deleted tests to disk
    """
    log.info(f"Creating dataset, with max_tm = {max_tm}")

    with open(TESTCONFIG_ROOT / f"{repo_name}.json", "r") as f:
        repo_config = json.loads(f.read())        

    base_path = out_repo if out_repo else src_repo.repo_path
    total_deleted = 0
    failed_mod = 0
    processed_tm = 0
    deleted_per_module = defaultdict(int)
    
    for test_file in src_repo.test_files:        
        for tm in [tm for tm in test_modules if tm.test_file == test_file]:
            if max_tm and processed_tm >= max_tm:
                break

            try:
                tm_deleted = 0
                to_exclude = []
                num_to_del = num_delete(tm, to_keep=to_keep, to_delete=to_delete)
                if num_to_del < 3:
                    log.info(f"Skipping {tm.name} as no tests to delete")
                    raise NoTestsToDelete()

                og_contents = test_file.to_code()
            
                log.info(f"Deleting {num_to_del} tests from {tm.name}")
                # we take the module coverage before and after the unit tests have been rmeoved
                # to calcuate the difference in coverage
                modcov_before = await run_test_local(repo_name, None, include_tests=[tm.name], use_cache=False)
                for func in tm.tests[:num_to_del]:
                    to_exclude.append((func, tm.test_file.path))
                    src_repo.find_file(tm.path).delete(
                        func.name, node_type=NodeType.Function
                    )
                    deleted_per_module[tm.name] += 1
                    total_deleted += 1
                    tm_deleted += 1

                # write deleted test_file contents to disk and measure coverage diff
                file_contents = test_file.to_code()
                with open(base_path / test_file.path, "w", encoding="utf-8") as f:
                    f.write(file_contents)

                log.info(f"OG file content length: {len(og_contents)}")
                log.info(f"New file content length: {len(file_contents)}")

                modcov_after = await run_test_local(repo_name, None, include_tests=[tm.name], use_cache=False)
                diff_cov = modcov_before.get_coverage() - modcov_after.get_coverage()

                log.info(f"Diff coverage: {diff_cov.total_cov.covered}")
                row = TestModuleEvalData(
                    name=tm.name,
                    base_cov=base_cov,
                    file_content=file_contents,
                    module_cov=modcov_after.get_coverage(),
                    repo_config=repo_config,
                    expected=diff_cov.total_cov.covered,
                    tags=[tm.name]
                )
                row.persist(tm)

                # TODO: hitting limit for row size here with braintrust
                # dataset.update(
                #     tm.name,
                #     TestModuleRow(
                #         tm=tm,
                #         base_cov=base_cov,
                #         file_content=file_contents,
                #         module_cov=diff_cov,
                #         repo_config=repo_config,
                #         expected=diff_cov.total_cov.covered
                #     ).to_json(),
                #     tags=[tm.name]
                # )

                log.info(f"Updating dataset with: {tm.name}")

                processed_tm += 1
                log.info(f"Deleted {tm_deleted} tests from {tm.name}")
                
            except Exception as e:
                raise e
                failed_mod += 1

        output_path = base_path / test_file.path
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Print summary of affected modules
    summary = "\nSummary of affected modules:\n"
    for module, count in deleted_per_module.items():
        summary += f"  {module}: {count} tests deleted\n"
    
    summary += f"\nTotal tests deleted: {total_deleted}\n"
    summary += f"Total failed: {failed_mod}"
    with open(base_path / "neuter_summary.txt", "w") as f:
        f.write(summary)

async def get_target_coverage(repo_name: str, 
                              src_repo: SourceRepo, 
                              base_cov: TestCoverage,
                              test_module: TestModule):
    chunks = await get_tm_target_coverage(
        repo_name=repo_name,
        src_repo=src_repo,
        tm=test_module,
        base_cov=base_cov,
        run_test=run_test_local,
        run_args=None
    )
    test_module.chunks = chunks