from src.repo.models import RepoConfig
from src.runner.local.run_test import run_test
from src.test_modules.iter_tms import iter_test_modules

from tests.utils import GitCommitContext
from cowboy_lib.repo import SourceRepo

import pytest

pytestmark = pytest.mark.asyncio

async def test_module_cov_tm_file_no_class(test_repoconfig: RepoConfig, source_repo: SourceRepo):
    """Test collecting coverage for a single module"""

    math_tm = iter_test_modules(source_repo, lambda tm: tm.name == "test_math_utils.py")[0]

    with GitCommitContext(source_repo.repo_path, 
                          "bbef16d68d0a01b3af6bb785bd8b4d0250ce37b1"):
        module_cov = await run_test(
            "testrepo",
            None,
            include_tests=math_tm,
            use_cache=False
        )
        
        math_cov = [
            cov for cov in module_cov.get_coverage().cov_list 
            if cov.filename == "math_utils.py"
        ][0]
        
        assert math_cov.covered == 25
        
        assert module_cov.get_coverage().total_cov.covered == 26    
        assert module_cov.get_coverage().total_cov.misses == 24
        assert module_cov.get_coverage().total_cov.stmts == 50

async def test_module_cov_tm_file_class(test_repoconfig: RepoConfig, source_repo: SourceRepo):
    """Test collecting coverage for a single module"""

    b_tm = iter_test_modules(source_repo, lambda tm: tm.name == "test_b.py")[0]

    with GitCommitContext(source_repo.repo_path, 
                          "e483b460318bf6bed6585c71cc68895185609109"):
        module_cov = await run_test(
            "testrepo",
            None,
            include_tests=b_tm,
            use_cache=False
        )
        
        math_cov = [
            cov for cov in module_cov.get_coverage().cov_list 
            if cov.filename == "b.py"
        ][0]
        
        # assert math_cov.covered == 25
        
        # assert module_cov.get_coverage().total_cov.covered == 26    
        # assert module_cov.get_coverage().total_cov.misses == 24
        # assert module_cov.get_coverage().total_cov.stmts == 50

async def test_test_files_excluded_in_coverage():
    FORBIDDEN_FILES = [
        "tests/test_a.py", 
        "tests/test_math_utils.py",
        "tests/test_string_utils.py"
    ]

    base_cov = await run_test(
        "testrepo",
        None,
        use_cache=False
    )

    for cov in base_cov.get_coverage().cov_list:
        assert cov.filename not in FORBIDDEN_FILES