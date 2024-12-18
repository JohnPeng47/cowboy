import dotenv
from typing import Dict
from pathlib import Path
from cowboy_lib.repo import SourceRepo
from braintrust import EvalAsync
import git
import yaml

from src.test_gen.augment_test.composer import Composer
from src.runner.local.run_test import run_test
from src.config import COWBOY_OPENAI_API_KEY

from .datasets import TestModuleRow, read_rows

dotenv.load_dotenv()

# Lets move all parameters into the input
EVAL_OUTPUT = Path("src/eval/output")

## Scoring functions
def coverage(output: Dict, expected: int):
    """
    Coverage improvement out of total possible expected coverage (sum of all coverage 
    from neutered tests)
    """
    cov_added = output["cov_added"]

    print(f"Cov added: {cov_added} / {expected}")
    return cov_added / expected

def improved_tests(output: Dict, expected: int):
    """
    Number of tests improved out of total possible expected tests
    """
    improved = output["improved"]
    no_improve = output["no_improve"]
    failed = output["failed"]

    return improved / (improved + no_improve + failed)

#############

async def eval_augment(data: Dict):
    repo_data = TestModuleRow.from_json2(data)  

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
    output_dir = EVAL_OUTPUT / repo_data.repo_config["repo_name"]
    cov_added = 0

    git_hash = git.Repo(src_repo.repo_path).head.commit.hexsha
    yaml_output = {
        "git_hash": git_hash,
        "tests": []
    }

    for test, test_cov in improved:
        cov_added += test_cov.total_cov.covered
        test_data = {
            "name": test.name,
            "coverage_added": test_cov.total_cov.covered,
            "test_module": tm.name,
            "code": test.to_code(),
        }
        yaml_output["tests"].append(test_data)

    yaml_str = yaml.dump(yaml_output, sort_keys=False)
    with open(output_dir / f"{tm.name}.yml", "w") as f:
        f.write(yaml_str)

    return {
        "new_tests": yaml_output["tests"],
        "cov_added": cov_added,
        "improved": len(improved),
        "failed": len(failed_tests),
        "no_improve": len(no_improve_tests)
    }
    
async def eval_dataset(repo_name: str, 
                      num_records: int = 0,
                      strat: str = "WITH_CTXT",
                      evaluator: str = "ADDITIVE",
                      n_times: int = 2):
    """
    Evaluate the dataset locally
    """
    dataset = [datum.to_json() for datum in read_rows(repo_name)]
    num_records = len(dataset) if num_records == 0 else num_records    

    datasetnames = ",".join([datum["input"]["name"] for datum in dataset[:num_records]])
    print("Evaluating TestModules => ", datasetnames)

    for dataset in dataset[:num_records]:
        await eval_augment(dataset, strat=strat, evaluator=evaluator, n_times=n_times)

async def eval_dataset_braintrust(repo_name: str, 
                                num_records: int = 0,
                                strat: str = "WITH_CTXT",
                                evaluator: str = "ADDITIVE",
                                n_times: int = 2):
    """
    Evaluate the dataset locally and save results to braintrust
    """    
    # NEWTODO: use bt dataset
    # dataset = init_dataset(project="Cowboy", name=dataset_name, api_key=BRAINTRUST_API_KEY)
    dataset = [datum.to_json() for datum in read_rows(repo_name)]
    for d in dataset:
        d["input"].update({
            "strat": strat,
            "evaluator": evaluator,
            "n_times": n_times
        })
    
    num_records = len(dataset) if num_records == 0 else num_records
    datasetnames = ",".join([datum["input"]["name"] for datum in dataset[:num_records]])
    print("Evaluating TestModules => ", datasetnames)

    # NOTE: Braintrust eval expects a list of dicts
    await EvalAsync(
        repo_name,
        dataset[:num_records],
        eval_augment,
        [coverage, improved_tests],
        experiment_name = f"{repo_name}::{strat}::{n_times}_n_times::{len(dataset[:num_records])}_TMs"
    )