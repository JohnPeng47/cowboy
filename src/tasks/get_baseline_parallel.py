from cowboy_lib.repo.source_repo import SourceRepo
from cowboy_lib.coverage import Coverage, TestCoverage, CoverageResult
from cowboy_lib.test_modules.test_module import TestModule, TargetCode
from cowboy_lib.utils import testfiles_in_coverage

from src.queue.core import TaskQueue
from src.runner.service import RunServiceArgs
from src.logger import buildtm_logger as log

from typing import List, Tuple, Callable
from pathlib import Path
import asyncio
from collections import defaultdict

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

    # if testfiles_in_coverage(base_cov, src_repo):
    #     raise TestInCoverageException

    # First loop we find the total coverage of each test by itself
    only_module = [tm.name]
    # coverage with ONLY the current test module turned on
    log.info(f"Collecting target chunks for {tm.name}")

    # TODO: should be storing this as well
    module_cov = await run_test(
        repo_name,
        run_args,
        # part1: collect the coverage of a single module only
        include_tests=only_module,
    )
    log.info(f"BaseCov: {base_cov}")
    log.info(f"ModuleCov: {module_cov.coverage}")

    module_diff = base_cov - module_cov.coverage
    total_cov_diff = module_diff.total_cov.covered
    if total_cov_diff > 0:
        chg_cov = []
        coroutines = []

        for test in tm.tests:
            print("Running test ... ", test.name)
            task = run_test(
                repo_name,
                run_args,
                # part 2:
                # holds the coverage diff of individual tests after they have
                # been selectively turned off
                exclude_tests=[(test, tm.test_file.path)],
                include_tests=only_module,
            )
            coroutines.append(task)

        test_coverage = defaultdict(int)
        cov_res = await asyncio.gather(*[t for t in coroutines])
        for test, test_cov in zip(tm.tests, cov_res):                
            print("ModuleCov: ", module_cov.coverage)
            print("Test cov: ", test_cov.coverage)
            
            # part 3: we subtract the module from the 
            single_diff: TestCoverage = module_cov.coverage - test_cov.coverage
            test_coverage[test.name] += single_diff.total_cov.covered

            # dont think we actually need this here .. confirm
            chg_cov.extend(single_diff.cov_list)

        # NEWTODO: potentially we should store this on a TestModel object
        # although we would first have to create that ...
        for test, coverage in test_coverage.items():
            log.info(f"{test} covered by {coverage} lines")

            # TBH, not sure why this happens
            if coverage < 0:
                log.warn(f"Coverage for {test} is negative: {coverage}")
              
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
