from src.test_modules.iter_tms import iter_test_modules
from cowboy_lib.repo.source_file import SourceFile
from cowboy_lib.repo.source_repo import SourceRepo

from tests.utils import GitCommitContext

def test_mixed_scope_funcs(source_repo: SourceRepo):
    with GitCommitContext(source_repo.repo_path, "5ddef6ba9fa97cf11fa76cdcbe0d5234baba77c2"):
        tms = iter_test_modules(source_repo, 
                                lambda tm: tm.name == "test_serializer.py")