import sys
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
from src.repo.models import RepoConfig
from src.auth.service import get_or_create_admin_user
from src.repo.service import get_or_create_local as get_or_create_repo
from src.config import REPOS_ROOT, BRAINTRUST_API_KEY, BT_PROJECT, TESTCONFIG_ROOT
from src.test_modules.iter_tms import iter_test_modules
from src.database.core import engine
from src.runner.local.run_test import get_repo_config, run_test as run_test_local

from src.logger import buildtm_logger as log

from .datasets import TestModuleRow, persist_rows, read_rows

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

    with open(Path(TESTCONFIG_ROOT) / f"{repo_name}.json", "r") as f:
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
                    # NEWTODO: we should track this number in the state somwhere
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
                row = TestModuleRow(
                    tm=tm,
                    base_cov=base_cov,
                    file_content=file_contents,
                    module_cov=modcov_after.get_coverage(),
                    repo_config=repo_config,
                    expected=diff_cov.total_cov.covered
                )
                persist_rows(row, repo_name)

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

# def get_or_create_repo_from_conf(repo_name: str) -> RepoConfig:
#     repo_conf = get_repo_config(repo_name)
#     with Session() as session:
#         user = get_or_create_admin_user(db_session=session)
#         repo, base_cov = get_or_create_repo(db_session=session, 
#                                user_id=user.id,  
#                                repo_in=repo_conf, 
#                                task_queue=None)
#         session.commit()

#         return repo, base_cov

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

if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="Neuter a repository by removing test functions while keeping a specified number"
    )
    parser.add_argument(
        "repo_name",
        type=str,
        help="Name of the repo config file"
    )
    parser.add_argument(
        "--out-repo",
        type=str,
        help="Optional path to output neutered repository (defaults to modifying original)",
        default=None
    )
    parser.add_argument(
        "--keep",
        type=int,
        help="Number of test functions to keep per module (default: 2)",
        default=2
    )
    parser.add_argument(
        "--delete",
        type=int,
        help="Number of test functions to delete per module (default: 0, meaning keep specified number)",
        default=0
    )
    parser.add_argument(
        "--max-tm",
        type=int,
        help="Maximum number of test modules to process",
        default=5
    )
    args = parser.parse_args()
    # res = asyncio.run(get_or_create_repo_from_conf(args.repo_name))
    repo = get_repo_config(args.repo_name)
    base_cov = asyncio.run((run_test_local(repo.repo_name, None)))
    base_cov = base_cov.get_coverage()

    log.info(f"#### Create Dataset for {repo.repo_name} ####")
    
    print("BaseCov: ", base_cov)
    
    dataset = init_dataset(name=repo.repo_name, project=BT_PROJECT, api_key=BRAINTRUST_API_KEY)

    print("iniitlaized dataset: ", repo.repo_name)

    out_repo = Path(args.out_repo) if args.out_repo else None
    src_repo = SourceRepo(Path(repo.source_folder))
    test_modules = iter_test_modules(src_repo)
    
    current_module = 0
    while current_module < min(len(test_modules), args.max_tm):
        try:
            print("__________________________________________________________________")
            print("Current module: ", current_module)
            print("__________________________________________________________________")
            
            tm = test_modules[current_module]
            asyncio.run(get_target_coverage(repo.repo_name, src_repo, base_cov, tm))
            asyncio.run(
                neuter_repo(
                    dataset,
                    repo.repo_name,
                    [tm],
                    src_repo, 
                    base_cov=base_cov,
                    to_keep=args.keep, 
                    to_delete=args.delete,
                    max_tm=1,
                    out_repo=out_repo
                )
            )

            current_module += 1
        except Exception as e:
            log.error(f"Error processing module {current_module}: {e}")
            test_modules = test_modules[1:]
            continue
    
