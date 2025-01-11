from cowboy_lib.repo.source_repo import SourceRepo
from cowboy_lib.coverage import Coverage, TestCoverage, CoverageResult
from cowboy_lib.test_modules.test_module import TestModule, TargetCode

from src.queue.core import TaskQueue
from src.runner.service import RunServiceArgs
from src.logger import buildtm_logger as log

from typing import List, Tuple, Callable
from pathlib import Path
import asyncio
from collections import defaultdict

REPO_STATE_RESET_MSG = """
Abnormally large coverage difference found, possible that you did not reset the repo state
after running setup-eval-repo. Try to `git reset --hard` your target repo and run this again
"""

class BigDiff(Exception):
    pass

class TestInCoverageException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = "Test files are included in coverage report"

def set_chunks(
    changed_coverage: List[Coverage],
    source_repo: "SourceRepo",
    base_path: Path = None,
) -> List[TargetCode]:
    """
    Gets the missing/covered lines of each of the coverage differences
    """
    chunks = []
    for cov in changed_coverage:
        if cov.filename == "TOTAL":
            raise Exception("TOTAL COVERAGE FILE FOUND")

        cov.read_line_contents(base_path)
        for l_group in cov.get_contiguous_lines():
            start = l_group[0][0]
            end = l_group[-1][0]
            range = (start, end)

            src_file = source_repo.find_file(cov.filename)
            func, cls = src_file.map_line_to_node(start, end)

            lines = [g[1] for g in l_group]

            # print("Setting chunk with filepath: ", str(cov.filename))

            chunk = TargetCode(
                range=range,
                lines=lines,
                # could also just move the logic into TestModuleMixin
                filepath=str(cov.filename),
                func_scope=func if func else "",
                class_scope=cls if cls else "",
            )
            chunks.append(chunk)

    return chunks

def compare(base_cov: TestCoverage, module: TestCoverage):
    for cov1, cov2 in zip(base_cov.cov_list, module.cov_list):
        print(cov1.filename, cov2.filename)
        if cov1.stmts != cov2.stmts:
            print("Different stmts ")


async def get_tm_target_coverage(
    repo_name: str,
    src_repo: SourceRepo,
    tm: TestModule,
    base_cov: TestCoverage,
    run_test: Callable,
    run_args: RunServiceArgs,
) -> List[TargetCode]:
    """
    Test augmenting existing test classes by deleting random test methods, and then
    having LLM strategy generate them. Coverage is taken:
    1. After the deletion
    2. After the deletion with newly generated LLM testcases

    The diff measures how well we are able to supplant the coverage of the deleted methods
    """

    # First loop we find the total coverage of each test by itself
    only_module = tm
    log.info(f"Collecting target chunks for {tm.name}")

    # TODO: should be storing this as well
    module_cov = await run_test(
        repo_name,
        run_args,
        # part1: collect the coverage of a single module only
        include_tests=only_module,
        # stream = True,
        use_cache=False,
        delete_last=False
    )
    # log.info(f"BaseCov: {base_cov}")
    # log.info(f"ModuleCov: {module_cov.get_coverage()}")

    module_diff = base_cov - module_cov.get_coverage()
    total_cov_diff = module_diff.total_cov.covered
    if total_cov_diff > 0:
        chg_cov = []
        coroutines = []

        for test in tm.tests:
            task = run_test(
                repo_name,
                run_args,
                # part 2:
                # holds the coverage diff of individual tests after they have
                # been selectively turned off
                exclude_tests=[(test, tm.test_file.path)],
                include_tests=only_module,
                # stream = True,
                use_cache=False,
                delete_last=False
            )
            coroutines.append(task)

        total_covered = 0
        test_coverage = defaultdict(int)
        cov_res = await asyncio.gather(*[t for t in coroutines])
        for test, test_cov in zip(tm.tests, cov_res): 
            # log.info(f"Collecting coverage for test: {test.name}")  
            # log.info(f"ModuleCov: {module_cov.get_coverage()}")
            # log.info(f"TestCov: {test_cov.get_coverage()}")
            
            # part 3: we subtract the module from the 
            single_diff: TestCoverage = module_cov.get_coverage() - test_cov.get_coverage()
            if single_diff.total_cov.covered > 0:
                if single_diff.total_cov.covered > 1000: # BIG DIFF
                    # log.error("Big diff found")
                    raise Exception(REPO_STATE_RESET_MSG)
                
                test_coverage[test.name] = single_diff.total_cov.covered
                total_covered += single_diff.total_cov.covered
                chg_cov.extend(single_diff.cov_list)
            else:
                continue

        print(f"Total covered for {tm.name}: ", total_covered)
        # re-init the chunks according to the aggregated individual test coverages
        chunks = set_chunks(
            chg_cov,
            source_repo=src_repo,
            base_path=src_repo.repo_path,
        )

    # Find out what's the reason for the missed tests
    else:
        log.info(f"No coverage difference found for {tm.name}")
        return []

    return chunks