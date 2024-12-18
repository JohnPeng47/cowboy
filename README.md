## Cowboy
An test generator using LLMs and code coverage to automatically extend your pre-existing test suites. Completely handsoff after initial config, point it at a repo and sit back and watch your coverage go up, up, up!\
_Intended to be language agnostic but currently Python/pytest support only_

## How it works
LLMs are the core component and it requires two pieces of context to extend a unit test suite:\
1. The currently existing tests
2. The source file(s) that the tests cover
(1) is given and (2) can be inferred from the unique coverage contributed by a test suite. More info on this in docs/detailed.txt.

Cowboy will automatically detect every testsuite in your repo, and for each one, will generate a series of new tests; only those that improve coverage are kept. This prunes away failed/non-improving tests and ensuring high quality test generation.

## How to run
1. First define a config for your repo in src/eval/configs/<repo_name>.json
```
{
    "repo_name": "codecovapi-neutered",                    # Name of config, needs to match filename of repo
    "url": "https://github.com/codecov/codecov-api.git",   
    "source_folder": "/home/ubuntu/codecov-api",           # Local path to your git repo
    "cloned_folders": ["/home/ubuntu/codecov-api"],        # Can be same as above, but can also create multiple folders so Cowboy can                                                              # use them to speed up its coverage collection process
    
    "python_conf": {                                       # Pytest Specific Configs
        "cov_folders": ["./"],                             
        "interp": "docker-compose exec api python",        # Interpreter command, executed in the source_folder of your repo
                                                           # Cowboy will do some like: <interp> -m pytest --cov <cov_folders> .. 
        "test_folder": ".",
        "pythonpath": ""
    }
}
```
2. Next, create datasets (testsuites + coverage info) with:
```
python -m src.eval.cli create-dataset <repo_name>
```
This step can take a while, especially the first time (what it's doing is explained in docs/detailed.txt)

....
TBA

## Evaluations
A pre-generated evaluation run against the [codecov-api](https://github.com/codecov/codecov-api) can be found [here](https://www.braintrust.dev/app/Cowboy/p/codecovapi-neutered/experiments/codecovapi-neutered%3A%3AWITH_CTXT%3A%3A2_n_times%3A%3A5_TMs?c=codecovapi-neutered::WITH_CTXT::3_n_times::1_TMs).



