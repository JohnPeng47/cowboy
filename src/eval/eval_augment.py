import dotenv
import os
from typing import Dict, Tuple
from braintrust import init_dataset, EvalAsync
from pathlib import Path
import asyncio
from cowboy_lib.repo import SourceRepo, GitRepo
import argparse

from src.repo.models import RepoConfig
from src.test_gen.augment_test.composer import Composer
from src.auth.service import retrieve_oai_key
from src.runner.service import RunServiceArgs
from src.runner.local.run_test import get_repo_config, run_test
from src.config import COWBOY_OPENAI_API_KEY, BRAINTRUST_API_KEY, EVAL_DATA_ROOT

from .datasets import TestModuleRow, read_rows
from .utils import write_test_results

dotenv.load_dotenv()

EVAL_OUTPUT = Path("src/eval/output")

def score(output: Tuple, expected: int):
    tests, cov_added = output

    print(f"Cov added: {cov_added} / {expected}")
    return cov_added / expected

async def eval_augment(data: Dict):
    # data = TestModuleRow.from_json2(data)
    data = TestModuleRow.from_json(data)
    src_repo = SourceRepo(Path(data.repo_config["source_folder"]))
    composer = Composer(
        repo_name=data.repo_config["repo_name"],
        strat="WITH_CTXT",
        evaluator="ADDITIVE",
        src_repo=src_repo,
        test_input=data.tm,
        run_args=None,
        api_key=COWBOY_OPENAI_API_KEY,
        run_test=run_test
    )
    improved, failed_tests, no_improve_tests = await composer.generate_test(
        n_times=3
    )
    all_tests = ""
    cov_added = 0

    output_dir = EVAL_OUTPUT / data.repo_config["repo_name"]
    write_test_results(output_dir, data.tm.name, improved)

    return all_tests, cov_added
    
async def eval_dataset(repo_name: str, 
                       dataset_name: str, 
                       num_records: int = 0):
    """
    Evaluate the dataset locally
    """
    dataset = [datum.to_json() for datum in read_rows(repo_name)]
    num_records = len(dataset) if num_records == 0 else num_records

    print(f"Using {num_records} of {dataset_name}")

    for dataset in dataset[:num_records]:
        await eval_augment(dataset)

async def eval_dataset_braintrust(repo_name: str, 
                       dataset_name: str, 
                       num_records: int = 0):
    """
    Evaluate the dataset locally and save results to braintrust
    """    
    # dataset = init_dataset(project="Cowboy", name=dataset_name, api_key=BRAINTRUST_API_KEY)
    dataset = [datum.to_json() for datum in read_rows(repo_name)]
    num_records = len(dataset) if num_records == 0 else num_records

    print(f"Using {num_records} of {dataset_name}")
    for dataset in dataset[:num_records]:
        await EvalAsync(
            repo_name,
            dataset[:num_records],
            eval_augment,
            [score]
        )

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate test augmentation on datasets")
    parser.add_argument(
        "repo_name",
        type=str,
        help=f"Name of the repository folder under {EVAL_DATA_ROOT}"
    )
    parser.add_argument(
        "dataset_name",
        type=str,
        help="Name of the dataset in Braintrust (if using --use-braintrust)"
    )
    parser.add_argument(
        "--num-records",
        type=int,
        default=0,
        help="Number of records to evaluate (0 for all)"
    )
    parser.add_argument(
        "--braintrust",
        action="store_true",
        default=False,
        help="Whether to use Braintrust for evaluation"
    )
    
    return parser.parse_args()

async def main():
    args = parse_args()
    
    if args.braintrust:
        await eval_dataset_braintrust(args.repo_name, args.dataset_name, args.num_records)
    else:
        await eval_dataset(args.repo_name, args.dataset_name, args.num_records)

if __name__ == "__main__":
    asyncio.run(main())

