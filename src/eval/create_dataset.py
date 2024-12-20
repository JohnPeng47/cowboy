import json
from typing import List
from pathlib import Path
from collections import defaultdict
from sqlalchemy.orm import sessionmaker
from braintrust import Dataset

from cowboy_lib.coverage import TestCoverage
from cowboy_lib.test_modules import TestModule
from cowboy_lib.ast import NodeType

from src.config import TESTCONFIG_ROOT
from src.database.core import engine
from src.runner.local.run_test import run_test as run_test_local
from src.local.models import TestModuleEvalData
from src.logger import buildtm_logger as log
from src.utils import confirm_action

class NoTestsToDelete(Exception):
    pass

# Create a session factory (similar to main.py)
Session = sessionmaker(bind=engine)

def num_delete(tm: TestModule, to_keep: int = 1, to_delete: int = 1) -> int:
    if to_keep and to_delete:
        raise Exception("Cannot have both values > 0")
    
    log.info(f"Tests to delete [{tm.name}]: ")
    for test in tm.tests:
        log.info(f"{test.name}, {tm.test_file.path}")

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
    repo_path: Path, 
    base_cov: TestCoverage,
    to_keep, 
    to_delete=0,
    ask_confirm=True,
):
    """
    Iterate TestModules and delete tests from each according to to_keep/to_delete. 
    Process up to max_tm test modules. Writes summary of deleted tests to disk
    """
    with open(TESTCONFIG_ROOT / f"{repo_name}.json", "r") as f:
        repo_config = json.loads(f.read())        

    base_path = repo_path
    total_deleted = 0
    failed_mod = 0
    processed_tm = 0
    deleted_per_module = defaultdict(int)
    
    for tm in test_modules:
        try:
            tm_deleted = 0
            to_exclude = []
            num_to_del = num_delete(tm, to_keep=to_keep, to_delete=to_delete)
            if num_to_del < 3:
                log.info(f"Skipping {tm.name} as no tests to delete")
                raise NoTestsToDelete()

            og_contents = tm.test_file.to_code()
        
            log.info(f"Deleting {num_to_del} tests from {tm.name}")
            # we take the module coverage before and after the unit tests have been rmeoved
            # to calcuate the difference in coverage
            modcov_before = await run_test_local(repo_name, None, include_tests=[tm.name], use_cache=False)
            for func in tm.tests[:num_to_del]:
                to_exclude.append((func, tm.test_file.path))
                tm.test_file.delete(
                    func.name, node_type=NodeType.Function
                )
                deleted_per_module[tm.name] += 1
                total_deleted += 1
                tm_deleted += 1

            # write deleted test_file contents to disk and measure coverage diff
            neutered_testfile = tm.test_file.to_code()

            print(f"Deleted {tm_deleted} tests from {tm.name}")
            with open(base_path / tm.test_file.path, "w", encoding="utf-8") as f:
                f.write(neutered_testfile)

            log.info(f"OG file content length: {len(og_contents)}")
            log.info(f"New file content length: {len(neutered_testfile)}")

            modcov_after = await run_test_local(repo_name, None, include_tests=[tm.name], use_cache=False)
            diff_cov = modcov_before.get_coverage() - modcov_after.get_coverage()

            row = TestModuleEvalData(
                name=tm.name,
                file_content=neutered_testfile,
                repo_config=repo_config,
                expected=diff_cov.total_cov.covered,
                tags=[tm.name]
            )
            row.persist(tm)

            # HACK: need this because PatchFileContext in run_test_local resets the commit of the repo
            # in its __exit__ method
            with open(base_path / tm.test_file.path, "w", encoding="utf-8") as f:
                f.write(neutered_testfile)

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

            log.info(f"Diff coverage: {diff_cov.total_cov.covered}")
            log.info(f"Updating dataset with: {tm.name}")
            processed_tm += 1
            
        except Exception as e:
            raise e
            failed_mod += 1

    # Print summary of affected modules
    summary = "\nSummary of affected modules:\n"
    for module, count in deleted_per_module.items():
        summary += f"  {module}: {count} tests deleted\n"
    
    summary += f"\nTotal tests deleted: {total_deleted}\n"
    summary += f"Total failed: {failed_mod}"
    with open(base_path / "neuter_summary.txt", "w") as f:
        f.write(summary)