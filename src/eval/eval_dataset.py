import dotenv
from typing import Dict, List
from braintrust import EvalAsync

from src.local.augment_tests import extend_tests
from src.local.models import read_rows, TestModuleData, TestModuleEvalData

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
                       tm_datalist: List[Dict],
                       experiment_name: str):
    """
    Evaluate the dataset locally
    """

    for dataset in tm_datalist:
        await extend_tests(dataset)

async def eval_dataset_braintrust(repo_name: str, 
                                  tm_datalist: List[Dict],
                                  experiment_name: str):
    """
    Evaluate the dataset locally and save results to braintrust
    """    

    await EvalAsync(
        repo_name,
        tm_datalist,
        extend_tests,
        [score_coverage, score_improved_tests],
        experiment_name = experiment_name
    )