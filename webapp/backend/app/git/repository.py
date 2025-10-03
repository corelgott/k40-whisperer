from pathlib import Path
import git
from datetime import datetime

class GitRepository:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.repo = None
    
    def init(self):
        if not (self.project_dir / ".git").exists():
            self.repo = git.Repo.init(self.project_dir)
            self.repo.config_writer().set_value("user", "name", "K40 Whisperer").release()
            self.repo.config_writer().set_value("user", "email", "k40@localhost").release()
        else:
            self.repo = git.Repo(self.project_dir)
    
    def commit(self, message: str):
        if self.repo is None:
            self.init()
        
        self.repo.git.add(A=True)
        
        if self.repo.is_dirty():
            self.repo.index.commit(message)
    
    def get_history(self, max_count: int = 50):
        if self.repo is None:
            self.init()
        
        commits = []
        for commit in self.repo.iter_commits(max_count=max_count):
            commits.append({
                "hash": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": datetime.fromtimestamp(commit.committed_date).isoformat()
            })
        return commits
    
    def checkout(self, commit_hash: str):
        if self.repo is None:
            self.init()
        
        self.repo.git.checkout(commit_hash)
