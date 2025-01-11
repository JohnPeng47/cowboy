from .augment_base import AugmentTestStrategy
from .prompt import AugmentTestPromptWithCtxt
from ..types import CtxtWindowExceeded
from ..utils import get_current_git_commit

from src.logger import testgen_logger as log


class AugmentClassWithCtxtStrat(AugmentTestStrategy):
    """
    Provides the src code context from the source code file targeted by the
    test_module
    """
    def build_prompt(self) -> AugmentTestPromptWithCtxt:
        prompt = AugmentTestPromptWithCtxt()
        curr_commit = get_current_git_commit(self.src_repo.repo_path)

        test_code = self.test_module.get_test_code()
        test_fit = prompt.insert_line("test_code", test_code)
        if not test_fit:
            raise CtxtWindowExceeded("Test code too large to fit in prompt")

        # TODO: how to narrow the scope of this to class or even function
        # have ref to func/class node in TargetCode
        for fp in self.test_module.targeted_files():
            # NEWTODO: we should remove this check and rely on omit in .coveragerc to filter out unwanted test files
            # in the coverage
            if fp.match("tests/*") or fp.match("*/tests/*") or fp.match("test_*"):
                log.warn(f"Skipping test file {fp} because test file")
                continue

            log.info(f"Src file ctxt of {self.test_module.name}: {fp}")
            file = self.src_repo.find_file(fp)
            code_fit = prompt.insert_line("file_contents", file.to_code())

            if not code_fit:
                log.warn(f"File {fp} too large to fit in prompt")
                continue

        if not self.test_module.targeted_files():
            log.warn(
                f"No src files targeted by {self.test_module.name} found")

        self.prompt = prompt
        return prompt.get_prompt()
    
    def update_prompt(self, new_testfile: str):
        self.prompt.update_line("test_code", new_testfile)
        
        log.info(f"Updating prompt test_code to: {new_testfile}")

        return self.prompt.get_prompt()

    def get_test_code(self, test_file, nodes):
        test_code = ""
        for node in nodes:
            try:
                test_code += test_file.find_by_nodetype(
                    node.name, node_type=node.node_type
                ).to_code()
            except Exception as e:
                log.error(f"Error: {e}")
                continue

        return test_code
