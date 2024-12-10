import sqlite3
import hashlib
import json
import pickle
from functools import wraps
from pathlib import Path
from typing import Any, Optional

from cowboy_lib.coverage import CoverageResult
from cowboy_lib.repo.repository import PatchFile

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
DB_PATH = CACHE_DIR / "test_cache.db"

def init_cache():
    """Initialize the SQLite cache database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_cache (
            hash TEXT PRIMARY KEY,
            result BLOB
        )
    """)
    conn.commit()
    conn.close()

def compute_hash(repo_name: str, exclude_tests: list, include_tests: list, patch_file: Optional[PatchFile]) -> str:
    """Compute a hash of the input arguments"""
    hash_input = {
        "repo_name": repo_name,
        "exclude_tests": exclude_tests,
        "include_tests": include_tests,
        "patch": patch_file.patch if patch_file else None
    }

    # janky, idk why sometimes I pass string and sometimes Function
    if hash_input["include_tests"] and not isinstance(hash_input["include_tests"][0], str):
        hash_input["include_tests"] = [func.to_json() for func in hash_input["include_tests"]]
    if hash_input["exclude_tests"] and not isinstance(hash_input["exclude_tests"][0][0], str):
        hash_input["exclude_tests"] = [(func[0].to_json(), str(func[1])) for func in hash_input["exclude_tests"]]

    hash_str = json.dumps(hash_input, sort_keys=True)
    return hashlib.sha256(hash_str.encode()).hexdigest()

def read_cache(hash_key: str) -> Optional[CoverageResult]:
    """Read a result from the cache"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT result FROM test_cache WHERE hash = ?", (hash_key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return pickle.loads(row[0])
    return None

def save_cache(hash_key: str, result: CoverageResult):
    """Save a result to the cache"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO test_cache (hash, result) VALUES (?, ?)",
        (hash_key, pickle.dumps(result))
    )
    conn.commit()
    conn.close()

def cache_test_run(func):
    """Decorator to cache test run results"""
    @wraps(func)
    async def wrapper(
        repo_name: str,
        service_args: Any,
        exclude_tests: list = [],
        include_tests: list = [],
        patch_file: Optional[PatchFile] = None,
    ) -> CoverageResult:
        init_cache()
        cache_key = compute_hash(repo_name, exclude_tests, include_tests, patch_file)
        
        # Try to get from cache
        print(f"Returning from cache: {(repo_name, exclude_tests, include_tests)}")
        cached_result = read_cache(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Run the actual function if not in cache
        result = await func(repo_name, service_args, exclude_tests, include_tests, patch_file)
        if not cached_result:
            print(f"Saving to cache: {(repo_name, exclude_tests, include_tests)}")
            save_cache(cache_key, result)
        return result
        
    return wrapper