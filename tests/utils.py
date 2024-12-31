import git

class GitCommitContext:
    def __init__(self, repo_path, target_commit):
        self.repo = git.Repo(repo_path)
        self.target_commit = target_commit
        self.original_commit = self.repo.head.commit.hexsha

    def __enter__(self):
        self.repo.git.checkout(self.target_commit, force=True)
        self.repo.git.reset("--hard", self.target_commit)
        return self.repo

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.repo.git.reset("--hard", self.original_commit)