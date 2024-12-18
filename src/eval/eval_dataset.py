import dotenv
from typing import Dict
from braintrust import EvalAsync

from src.local.extend_tests import extend_tests
from src.local.models import read_rows

dotenv.load_dotenv()

## Scoring functions
def score_coverage(output: Dict, expected: int):
    """
    Coverage improvement out of total possible expected coverage (sum of all coverage 
    from neutered tests)
    """
    cov_added = output["cov_added"]

    print(f"Cov added: {cov_added} / {expected}")
    return cov_added / expected

def score_improved_tests(output: Dict, expected: int):
    """
    Number of tests improved out of total possible expected tests
    """
    improved = output["improved"]
    no_improve = output["no_improve"]
    failed = output["failed"]

    return improved / (improved + no_improve + failed)

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
        await extend_tests(dataset, strat=strat, evaluator=evaluator, n_times=n_times)

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
        extend_tests,
        [score_coverage, score_improved_tests],
        experiment_name = f"{repo_name}::{strat}::{n_times}_n_times::{len(dataset[:num_records])}_TMs"
    )