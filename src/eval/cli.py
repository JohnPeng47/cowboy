import asyncio
import click
from pathlib import Path
from typing import Optional
from braintrust import init_dataset
from functools import wraps

from cowboy_lib.repo import SourceRepo
from src.runner.local.run_test import run_test
from src.test_modules.iter_tms import iter_test_modules
from src.config import BT_PROJECT, BRAINTRUST_API_KEY

from .eval_dataset import eval_dataset, eval_dataset_braintrust
from .create_dataset import neuter_repo, get_target_coverage
from .db import get_repo


def coro(f):
    """Decorator to run async functions using click"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@click.group()
def cli():
    """CLI tool for test evaluation and repository neutering operations."""
    pass

@cli.command()
@click.argument("repo_name", type=str)
@click.option("--num-records", type=int, default=0, 
              help="Number of records to evaluate (0 for all)")
@click.option("--strat", type=str, default="WITH_CTXT",
              help="Strategy for test generation")
@click.option("--evaluator", type=str, default="ADDITIVE",
              help="Evaluator type")
@click.option("--n-times", type=int, default=2,
              help="Number of times to generate tests")
@click.option("--braintrust", is_flag=True, default=False,
              help="Whether to use Braintrust for evaluation")
@coro
async def evaluate(repo_name: str, num_records: int, strat: str, 
                  evaluator: str, n_times: int, braintrust: bool):
    """Evaluate test augmentation on datasets."""
    if braintrust:
        await eval_dataset_braintrust(
            repo_name, 
            num_records,
            strat=strat,
            evaluator=evaluator,
            n_times=n_times
        )
    else:
        await eval_dataset(
            repo_name, 
            num_records,
            strat=strat,
            evaluator=evaluator,
            n_times=n_times
        )

@cli.command()
@click.argument("repo_name", type=str)
@click.option("--out-repo", type=str, default=None,
              help="Optional path to output neutered repository")
@click.option("--keep", type=int, default=2,
              help="Number of test functions to keep per module")
@click.option("--delete", type=int, default=0,
              help="Number of test functions to delete per module")
@click.option("--max-tm", type=int, default=5,
              help="Maximum number of test modules to process")
@coro
async def create_dataset(repo_name: str, out_repo: Optional[str], 
                        keep: int, delete: int, max_tm: int):
    """Neuter a repository by removing test functions."""
    repo = get_repo(repo_name)
    base_cov = await run_test(repo.repo_name, None)
    base_cov = base_cov.get_coverage()
    
    dataset = init_dataset(
        name=repo.repo_name, 
        project=BT_PROJECT, 
        api_key=BRAINTRUST_API_KEY
    )

    out_repo_path = Path(out_repo) if out_repo else None
    src_repo = SourceRepo(Path(repo.source_folder))
    test_modules = iter_test_modules(src_repo)
    
    current_module = 0
    while current_module < min(len(test_modules), max_tm):
        try:
            tm = test_modules[current_module]
            await get_target_coverage(repo.repo_name, src_repo, base_cov, tm)
            await neuter_repo(
                dataset,
                repo.repo_name,
                [tm],
                src_repo, 
                base_cov=base_cov,
                to_keep=keep, 
                to_delete=delete,
                max_tm=1,
                out_repo=out_repo_path
            )
            current_module += 1
        except Exception as e:
            click.echo(f"Error processing module {current_module}: {e}", err=True)
            test_modules = test_modules[1:]
            continue

def main():
    """Entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()