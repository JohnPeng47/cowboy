from pathlib import Path
from typing import List, Optional, Set


from cowboy_lib.test_modules import TestModule
from cowboy_lib.repo.source_file import SourceFile, TestFile
from src.utils import (
    get_repo_head, 
    cyan_text, 
    dim_text, 
    green_text
)
from src.repo.models import RepoConfig

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
        raise TestApplyError(f"The head of the repo ({src_commit_hash[:7]}) at {repo_config.source_folder} \
                             does not match the hash in the test results ({results.git_hash[:7]})")

    # # Get set of function names from TestFile
    # source_funcs: Set[str] = {f.name for f in source_file.test_funcs()}
    
    # # Get set of function names from TestModule
    # tm_funcs: Set[str] = {f.name for f in tm.test_file.test_funcs()}
    
    # # Check if the sets match
    # if source_funcs != tm_funcs:
    #     missing = tm_funcs - source_funcs
    #     extra = source_funcs - tm_funcs
    #     error_msg = []
    #     if missing:
    #         error_msg.append(f"Missing functions in source file: {missing}")
    #     if extra:
    #         error_msg.append(f"Extra functions in source file: {extra}")
    #     raise ValueError("\n".join(error_msg))

def print_test_summary(fp: Path, 
                       test_results: TestResults) -> None:
    """Print summary of test cases and their coverage improvements"""    
    total_coverage = 0
    summary = ""
    test_summary = ""
    
    summary += cyan_text(f"[{test_results.tm_name}]\n")
    for test in test_results.tests:
        test_name = test.name if len(test.name.split(".")) == 1 else test.name.split(".")[1]
        test_summary += f"{test_name} ---> coverage added: {green_text(test.coverage_added)}\n"
        total_coverage += test.coverage_added

    summary += dim_text(f"PatchFile: {fp}\n")
    summary += test_summary.rstrip() if test_summary else "No coverage improving tests added"
    summary += "\n\n"
    
    return summary


def confirm_action(prompt: str) -> bool:
    """Get user confirmation for an action"""
    while True:
        response = input(f"{prompt}\nDo you want to apply the patch (y/N): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no', '']:
            return False
        print("Please answer 'y' or 'n'")


def apply_tests(output_file: Path, target_file: Optional[Path] = None, repo_name: Optional[str] = None) -> None:
    """
    Parse test output and either print or apply the tests to a target file using SourceFile
    
    Args:
        output_file: Path to the test output file
        target_file: Optional path to write the parsed tests
        repo_name: Name of the repository (required for validation)
    """
    test_cases = parse_test_output(output_file)
    
    print(f"\nTest Module: {output_file.stem}")
    print("-" * 40)
    print_test_summary(test_cases)
    print("-" * 40)
    
    if target_file:
        if not confirm_action(f"Apply these tests to {target_file}?"):
            print("Operation cancelled")
            return
            
        # If target file exists, read it. Otherwise start with empty file
        if target_file.exists():
            with open(target_file, "r") as f:
                existing_lines = f.readlines()
        else:
            existing_lines = []
            
        source_file = TestFile(lines=existing_lines, path=target_file)
        
        # Append each test to the appropriate class or file
        for test in test_cases:
            # Add comments before the test
            comments = [
                f"# Test: {test.name}",
                f"# Coverage Added: {test.coverage}",
                f"# TestModule: {test.test_module}",
                ""
            ]
            
            # Try to find the test class and append to it
            try:
                source_file.append("\n".join(comments + [test.code]), class_name=test.test_module)
            except:
                # If class not found, append to end of file
                source_file.append("\n".join(comments + [test.code]))
        
        # Validate test functions if repo_name is provided
        if repo_name:
            for test in test_cases:
                validate_test_functions(source_file, test.test_module, repo_name)
        
        # Write the final contents
        with open(target_file, "w") as f:
            f.write(source_file.to_code())
        print(f"Successfully applied tests to {target_file}")
    else:
        # Just print if no target file
        for test in test_cases:
            print(f"# Test: {test.name}")
            print(f"# Coverage Added: {test.coverage}")
            print(f"# TestModule: {test.test_module}")
            print(test.code)
            print()