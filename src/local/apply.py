from pathlib import Path

from src.utils import (
    get_repo_head, 
    cyan_text, 
    dim_text, 
    green_text,
    red_text
)

from .db import get_tm, get_repo
from .models import TestCase, TestResults, TestModuleData

class TestApplyError(Exception):
    pass

def validate(results: TestResults) -> None:
    """
    Validate that the test functions in the source file match those in the TestModule
    """    
    repo_config = get_repo(results.repo_name)
    src_commit_hash = get_repo_head(repo_config.source_folder)
    if src_commit_hash != results.git_hash:
        raise TestApplyError(f"The head of the repo ({src_commit_hash[:7]}) at {repo_config.source_folder} does not match the hash in the test results ({results.git_hash[:7]})")

def print_test_summary(fp: Path, 
                       test_results: TestResults) -> None:
    """Print summary of test cases and their coverage improvements"""    
    total_coverage = 0
    summary = ""
    test_summary = ""
    tm = get_tm(test_results.repo_name, test_results.tm_name)
    
    summary += cyan_text(f"[{test_results.tm_name}]\n")
    for test in test_results.tests:
        test_name = test.name if len(test.name.split(".")) == 1 else test.name.split(".")[1]
        test_summary += f"{test_name} ---> coverage added: {green_text(test.coverage_added)}\n"
        total_coverage += test.coverage_added

    summary += dim_text(f"PatchFile: {fp}\n")
    summary += dim_text(f"TestFile: {tm.test_file.path}\n")
    summary += test_summary.rstrip() if test_summary else red_text("No coverage improving tests added")
    summary += "\n\n"
    
    return summary

def apply_tests(test_results: TestResults) -> None:             
    tm = get_tm(test_results.repo_name, test_results.tm_name) 
    repo_config = get_repo(test_results.repo_name)

    for test in test_results.tests:
        comments = f"# Coverage Added: {test.coverage_added}\n"

        try:
            tm.test_file.append(comments + test.code, class_name=tm.name if tm.name else None)
        except:
            tm.test_file.append(comments + test.code)
        
    print(f"Writing to {repo_config.source_folder / tm.test_file.path}: ")
    print(tm.test_file.to_code())

    # Write the final contents
    with open(repo_config.source_folder / tm.test_file.path, "w") as f:
        f.write(tm.test_file.to_code())

    print(f"Successfully applied tests to {tm.test_file.path}")