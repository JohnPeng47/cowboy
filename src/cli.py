import sys
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

from src.eval.eval_dataset import eval_dataset, eval_dataset_braintrust
from src.eval.create_dataset import neuter_repo
from src.local.db import get_repo, persist_tm, get_tm, DatasetCreationError
from src.local.models import TestResults, TestModuleData
from src.local.tgt_coverage import enrich_tm_with_tgt_coverage
from src.local.apply import (
    validate, 
    print_test_summary, 
    TestApplyError,
    apply_tests
)
from src.utils import confirm_action

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
@click.option("--keep", type=int, default=2,
              help="Number of test functions to keep per module")
@click.option("--delete", type=int, default=0,
              help="Number of test functions to delete per module")
@click.option("--max-tm", type=int, default=5,
              help="Maximum number of test modules to process")
@coro
async def setup_neutered_repo(repo_name: str, 
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
    src_repo = SourceRepo(Path(repo.source_folder))
    test_modules = iter_test_modules(src_repo)

    click.echo(f"Creating {max_tm}/{len(test_modules)} datasets")
    click.echo(f"Set \"--max-tm\" to change number of datasets to create")
    
    for tm in test_modules[:max_tm]:
        chunks = await enrich_tm_with_tgt_coverage(repo.repo_name, src_repo, base_cov, tm)
        tm.chunks = chunks

        await neuter_repo(
            dataset,
            repo.repo_name,
            [tm],
            Path(repo.source_folder), 
            base_cov=base_cov,
            to_keep=keep, 
            to_delete=delete,
        )
 
@cli.command()
@click.argument("repo_name", type=str)
@click.option("--max-tm", type=int, default=5,
              help="Maximum number of test modules to process")
@coro
async def setup_repo(repo_name: str, max_tm: int):
    """Setup a repo for local test augmentation"""
    repo = get_repo(repo_name)
    base_cov = await run_test(repo.repo_name, None)
    base_cov = base_cov.get_coverage()
    
    dataset = init_dataset(
        name=repo.repo_name, 
        project=BT_PROJECT, 
        api_key=BRAINTRUST_API_KEY
    )
    src_repo = SourceRepo(Path(repo.source_folder))
    test_modules = iter_test_modules(src_repo)

    click.echo(f"Creating {max_tm}/{len(test_modules)} datasets", fg="green")
    click.echo(f"Set \"--max-tm\" to change number of datasets to create", fg="yellow")
    
    current_module = 0
    while current_module < min(len(test_modules), max_tm):
        try:
            tm = test_modules[current_module]
            chunks = await enrich_tm_with_tgt_coverage(repo.repo_name, src_repo, base_cov, tm)
            tm.chunks = chunks

            tm_data = TestModuleData(
                name=tm.name,
                file_content=tm.test_file.to_code(),
                repo_config=repo.to_dict(),
            )
            tm_data.persist(tm)

            current_module += 1
        except Exception as e:
            click.echo(f"Error processing module {current_module}: {e}", err=True)
            test_modules = test_modules[1:]
            continue


@cli.command()
@click.argument("output_path", type=click.Path(exists=True, path_type=Path))
@coro
async def apply(output_path: Path):
    """Apply generated tests from output files to target files."""
    
    test_cases_str = ""
    non_empty = []
    for file in output_path.rglob("*.yml"):
        try:
            test_results = TestResults.from_file(file)
            validate(test_results)

            test_cases_str += print_test_summary(file, test_results)
            non_empty.append(test_results)

        except TestApplyError as e:
            click.echo(f"TestResult validation error: {e} => Skipping {file}", err=True)
            continue

    confirm = confirm_action(test_cases_str)
    if not confirm:
        sys.exit(1)

    for test_results in non_empty:
        apply_tests(test_results)

def main():
    """Entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()