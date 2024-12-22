from src.repo.models import RepoConfig
from src.runner.local.run_test import run_test

from cowboy_lib.repo import SourceRepo
import pytest

pytestmark = pytest.mark.asyncio

async def test_module_cov(test_repoconfig: RepoConfig, source_repo: SourceRepo):
    """Test collecting coverage for a single module"""

    module_cov = await run_test(
        "testrepo",
        None,
        include_tests=["test_math_utils.py"],
        use_cache=False
    )
    math_cov = [
        cov for cov in module_cov.get_coverage().cov_list 
        if cov.filename == "src/math_utils.py"
    ][0]
    
    assert math_cov.covered == 18
    
    assert module_cov.get_coverage().total_cov.covered == 24
    assert module_cov.get_coverage().total_cov.misses == 25
    assert module_cov.get_coverage().total_cov.stmts == 49

