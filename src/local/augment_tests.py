import git
import yaml
from typing import Dict
from pathlib import Path
from dataclasses import asdict
from cowboy_lib.repo import SourceRepo

from src.utils import get_repo_head
from src.test_gen.augment_test.composer import Composer
from src.runner.local.run_test import run_test
from src.config import COWBOY_OPENAI_API_KEY, EVAL_OUTPUT_ROOT

# should probably move this to another folder
from src.local.models import TestCase, TestResults, TestModuleData


async def extend_tests(data: Dict):
    repo_data = TestModuleData.from_json(data)  

    strat = data["strat"]
    evaluator = data["evaluator"]
    n_times = data["n_times"]
    tm = repo_data.get_tm()
    
    src_repo = SourceRepo(Path(repo_data.repo_config["source_folder"]))
    composer = Composer(
        repo_name=repo_data.repo_config["repo_name"],
        strat=strat,
        evaluator=evaluator,
        src_repo=src_repo,
        test_input=tm,
        run_args=None,
        api_key=COWBOY_OPENAI_API_KEY,
        run_test=run_test
    )
    improved, failed_tests, no_improve_tests = await composer.generate_test(
        n_times=n_times
    )
    output_dir = EVAL_OUTPUT_ROOT / repo_data.repo_config["repo_name"]
    cov_added = 0

    git_hash = get_repo_head(src_repo.repo_path)
    test_results = TestResults(
        repo_name=repo_data.repo_config["repo_name"],
        git_hash=git_hash,
        tm_name=tm.name,
        tests=[]
    )

    for test, test_cov in improved:
        cov_added += test_cov.total_cov.covered
        test_case = TestCase(
            name=test.name,
            coverage_added=test_cov.total_cov.covered,
            code=test.to_code()
        )
        test_results.tests.append(test_case)

    yaml_str = yaml.dump(asdict(test_results), sort_keys=False)
    with open(output_dir / f"{tm.name}.yml", "w") as f:
        f.write(yaml_str)

    return {
        "new_tests": [asdict(test) for test in test_results.tests],
        "cov_added": cov_added,
        "improved": len(improved),
        "failed": len(failed_tests),
        "no_improve": len(no_improve_tests)
    }