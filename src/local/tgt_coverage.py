from typing import List, Tuple

from cowboy_lib.repo import SourceRepo
from cowboy_lib.test_modules import TestModule

from src.utils import get_repo_head
from src.runner.local.run_test import run_test as run_test_local
from src.llm import LMP, LLMModel

from pydantic import BaseModel
from pathlib import Path

class SourceFiles(BaseModel):
    files: List[str]

class GuessSourceFiles(LMP):
    prompt = """
Given the following testcases:
{test_cases}

And the following list of files that are executed during the test along with their coverage:
{source_files}

Which filepaths are the actual intentional targets of the testcases above, rather than just being incidentally
covered during execution?
"""
    response_format = SourceFiles

    def _verify_or_raise(self, res: SourceFiles, **kwargs):
        source_files = kwargs["source_files"]

        for res_f in res.files:
            if not any(res_f == f[0] for f in source_files):            
                raise Exception(f"File returned from response: {res_f} does not exist in origin arg")


async def get_llm_file_coverage(repo_name: str, 
                              src_repo: SourceRepo, 
                              test_module: TestModule):
    module_cov = await run_test_local(
        repo_name,
        None,
        # part1: collect the coverage of a single module only
        include_tests=test_module,
        # stream = True,
        use_cache=False,
        delete_last=False
    )
    source_files = [(cov.filename, f"{(cov.covered / cov.stmts * 100):.2f}%") 
                     for cov in module_cov.get_coverage().cov_list if cov.stmts > 0]
    test_cases = test_module.get_test_code()

    model = LLMModel()
    guess_source = GuessSourceFiles()
    guess_source.invoke(model, 
                        "claude", 
                        source_files = source_files,
                        test_cases = test_cases)
    
    return 