import os
from typing import Dict, Tuple
from braintrust import init_dataset, EvalAsync
from pathlib import Path
from cowboy_lib.repo import SourceRepo, GitRepo

from src.repo.models import RepoConfig
from src.test_gen.augment_test.composer import Composer
from src.auth.service import retrieve_oai_key
from src.runner.service import RunServiceArgs
from src.runner.local.run_test import get_repo_config, run_test
from src.config import COWBOY_OPENAI_API_KEY, BRAINTRUST_API_KEY

from .datasets import TestModuleRow, read_rows
import dotenv

dotenv.load_dotenv()

def score(output: Tuple, expected: int):
    tests, cov_added = output
    return cov_added

async def eval_augment(data: Dict):
    data = TestModuleRow.from_json2(data)
    src_repo = SourceRepo(Path(data.repo_config["source_folder"]))
    composer = Composer(
        repo_name=data.repo_config["repo_name"],
        strat="WITH_CTXT",
        evaluator="ADDITIVE",
        src_repo=src_repo,
        test_input=data.tm,
        run_args=None,
        base_cov=data.base_cov,
        api_key=COWBOY_OPENAI_API_KEY,
        run_test=run_test
    )
    improved, failed_tests, no_improve_tests = await composer.generate_test(
        n_times=3
    )
    all_tests = ""
    cov_added = 0
    for testfile, cov_diff in improved:
        all_tests += testfile.to_code()
        cov_added += cov_diff.total_cov.covered

    return all_tests, cov_added
    
async def eval_dataset(repo_name: str, dataset_name: str):
    # dataset = init_dataset(project="Cowboy", name=dataset_name, api_key=BRAINTRUST_API_KEY)
    dataset = [datum.to_json() for datum in read_rows(repo_name)]
    await EvalAsync(
        repo_name,
        dataset,
        eval_augment,
        score
    )