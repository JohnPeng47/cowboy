from src.test_gen.augment_test.evaluators import AugmentAdditiveEvaluator
from src.repo.models import RepoConfig
from src.runner.service import RunServiceArgs
from src.runner.local.run_test import run_test
from src.test_gen.augment_test.types import StratResult
from src.local.db import get_tm

from cowboy_lib.repo import SourceRepo
import pytest
from pathlib import Path

pytestmark = pytest.mark.asyncio


TEST_MATH_UTILS = """
import pytest
from ..math_utils import factorial, is_prime, fibonacci

def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120

def test_factorial_errors():
    with pytest.raises(TypeError, match="Input must be an integer"):
        factorial(1.5)
    with pytest.raises(ValueError, match="Factorial is not defined for negative numbers"):
        factorial(-1)

def test_is_prime():
    assert is_prime(2) == True
    assert is_prime(3) == True
    assert is_prime(4) == False
    assert is_prime(17) == True
    assert is_prime(1) == False

def test_is_prime_errors():
    with pytest.raises(TypeError, match="Input must be an integer"):
        is_prime(1.5)

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(2) == 1
    assert fibonacci(5) == 5
    assert fibonacci(6) == 8

def test_fibonacci_errors():
    with pytest.raises(TypeError, match="Input must be an integer"):
        fibonacci(1.5)
    with pytest.raises(ValueError, match="Fibonacci is not defined for negative numbers"):
        fibonacci(-1) 
"""

async def test_additive_evaluator(test_repoconfig: RepoConfig, source_repo: SourceRepo):
    """Initialize AugmentAdditiveEvaluator with test repo"""

    math_utils_tm = get_tm("testrepo", "test_math_utils.py")    
    module_cov = await run_test(
        "testrepo",
        None,
        include_tests=["test_math_utils.py"],
        use_cache=False
    )

    # print(math_utils_tm.test_file.to_code())
    # for cov in module_cov.get_coverage().cov_list:
    #     print("Covered:" , cov.filename, cov.covered)
    #     # cov.read_line_contents(Path(test_repoconfig.source_folder))
    #     # print(cov.print_lines())

    # return
    
    evaluator = AugmentAdditiveEvaluator(
        repo_name=test_repoconfig.repo_name,
        src_repo=source_repo,
        run_args=None,
        tm=None,
        run_test=run_test,
    )
    improved, failed, no_improve = await evaluator(
        [StratResult(TEST_MATH_UTILS, "tests/test_math_utils.py")],
        math_utils_tm,
        module_cov.get_coverage(),
        math_utils_tm.test_file
    )

    assert len(improved) == 2