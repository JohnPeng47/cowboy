import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set
import argparse

from cowboy_lib.repo.source_file import SourceFile, TestFile

from .db import get_tm

@dataclass
class TestCase:
    name: str
    coverage: int
    test_module: str
    code: str
    git_hash: str = ""

def parse_test_output(file_path: Path) -> List[TestCase]:
    """
    Parse the test output file and extract test cases with their coverage info
    
    Args:
        file_path: Path to the test output file
        
    Returns:
        List of TestCase objects containing parsed test information
    """
    test_cases = []
    current_test = None
    current_code = []
    git_hash = ""
    
    with open(file_path, "r") as f:
        lines = f.readlines()
        
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("Git Hash:"):
            git_hash = line.replace("Git Hash:", "").strip()
            
        elif line.startswith("New Test:"):
            # Save previous test if exists
            if current_test and current_code:
                current_test.code = "\n".join(current_code)
                test_cases.append(current_test)
                current_code = []
            
            test_name = line.replace("New Test:", "").strip()
            current_test = TestCase(
                name=test_name,
                coverage=0,
                test_module="",
                code="",
                git_hash=git_hash
            )
            
        elif line.startswith("Coverage Added:"):
            if current_test:
                coverage = int(line.split(":")[-1].strip())
                current_test.coverage = coverage
                
        elif line.startswith("TestModule:"):
            if current_test:
                test_module = line.replace("TestModule:", "").strip()
                current_test.test_module = test_module
                
        else:
            # Collect code lines
            if current_test and line:
                current_code.append(line)
                
        i += 1
    
    # Add the last test case
    if current_test and current_code:
        current_test.code = "\n".join(current_code)
        test_cases.append(current_test)
        
    return test_cases


def validate_test_functions(source_file: TestFile, test_module_name: str, repo_name: str) -> None:
    """
    Validate that the test functions in the source file match those in the TestModule
    
    Args:
        source_file: The TestFile containing the test functions
        test_module_name: Name of the test module to validate against
        repo_name: Name of the repository
    """
    # Get the TestModule from disk
    tm = get_tm(repo_name, test_module_name)
    
    # Get set of function names from TestFile
    source_funcs: Set[str] = {f.name for f in source_file.test_funcs()}
    
    # Get set of function names from TestModule
    tm_funcs: Set[str] = {f.name for f in tm.test_file.test_funcs()}
    
    # Check if the sets match
    if source_funcs != tm_funcs:
        missing = tm_funcs - source_funcs
        extra = source_funcs - tm_funcs
        error_msg = []
        if missing:
            error_msg.append(f"Missing functions in source file: {missing}")
        if extra:
            error_msg.append(f"Extra functions in source file: {extra}")
        raise ValueError("\n".join(error_msg))


def print_test_summary(test_cases: List[TestCase]) -> None:
    """Print summary of test cases and their coverage improvements"""
    total_coverage = 0
    for test in test_cases:
        print(f"{test.name} ---> coverage added: {test.coverage}")
        total_coverage += test.coverage
    print(f"\nTotal coverage improvement: {total_coverage}")


def confirm_action(prompt: str) -> bool:
    """Get user confirmation for an action"""
    while True:
        response = input(f"{prompt} (y/N): ").lower().strip()
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


def parse_args():
    parser = argparse.ArgumentParser(description="Parse and apply generated tests")
    parser.add_argument(
        "repo_name",
        type=Path,
        help="Path to the test output file"
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="Optional path to write parsed tests",
        default=None
    )
    parser.add_argument(
        "--tm-name",
        type=str,
        help="TM name for validation",
        default=None
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    #1. CURSOR: recursively read all files in the output_path and 
    # For each file 
    output_path = Path(args.output_path)
    test_cases_str = ""

    for file in output_path.rglob("*.txt"):
        tm_name = file.stem
        test_cases = parse_test_output(file)
        test_cases_str += print_test_summary(test_cases)
        test_cases_str += "\n"
        
    # confirm_action(f"Apply these these testcases to the file : {}")
    apply_tests(args.output_file, args.target, args.repo_name)
