## Cowboy
An test generator using LLMs and code coverage to automatically extend your pre-existing test suites. Completely handsoff after initial config, point it at a repo and sit back and watch your coverage go up, up, up!\
_Intended to be language agnostic but currently Python/pytest support only_

Here are some evaluation results from running this on codecovapi (more detailed discussion of evaluations in docs/evaluations.txt):\
https://www.braintrust.dev/app/Cowboy/p/codecovapi-neutered/experiments/codecovapi-neutered%3A%3AWITH_CTXT%3A%3A2_n_times%3A%3A5_TMs-f8f7dc77?c=codecovapi-neutered::WITH_CTXT::2_n_times::5_TMs-6e7da49f&r=4772119f-2497-4a74-9694-f3bb64d63a77&tc=6b886f04-d019-4d6d-8e6d-5e88f09a45eb&s=90a3ff82-28cb-4169-9021-b05b09d2c4bc&diff=off|between_experiments

## How it works
LLMs are the core component and it requires two pieces of context to extend a unit test suite:
1. The currently existing tests
2. The source file(s) that the tests cover
(1) is given and (2) can be inferred using a novel coverage diffing algorithm (**more info on this in docs/detailed.txt.**)

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
2. Next, we need to collect some coverage info and store it on disk. This can be done by running:
```
python -m src.eval.cli setup-repo <repo_name>     # repo_name is the same as above
```
This step can take a while, especially the first time because we need to collect base coverage (for all testsuites). On subsequent runs, this is cached\

Can also specify the `--num-tms` argument to only collect data for a subset of TestModules (a set of unit tests representing either a file or class)
```
python -m src.eval.cli setup-repo <repo_name> --num-tms 1 
```
3. Once repo setup has finished, Cowboy generates some JSON data files in `src/eval/datasets/<repo_name>`. Each TestModule -> JSON file:
```
ubuntu@ip-172-31-37-242:~/cowboy-server$ ls -la src/eval/datasets/codecovapi-neutered/
total 52
drwxrwxr-x 3 ubuntu ubuntu 4096 Dec 20 01:15 .
drwxrwxr-x 5 ubuntu ubuntu 4096 Dec 22 09:41 ..
-rw-rw-r-- 1 ubuntu ubuntu 7020 Dec 20 14:04 GithubEnterpriseWebhookHandlerTests.json
-rw-rw-r-- 1 ubuntu ubuntu 5232 Dec 20 13:25 TestBitbucketServerWebhookHandler.json
-rw-rw-r-- 1 ubuntu ubuntu 5298 Dec 20 13:32 TestBitbucketWebhookHandler.json
-rw-rw-r-- 1 ubuntu ubuntu 6146 Dec 23 17:50 TestGitlabEnterpriseWebhookHandler.json
-rw-rw-r-- 1 ubuntu ubuntu 4223 Dec 20 13:41 TestGitlabWebhookHandler.json
drwxrwxr-x 2 ubuntu ubuntu 4096 Dec 20 01:15 tms
```

Now run `evaluate` command to generate the test cases:
```
python -m src.eval.cli evaluate <repo_name> --num-tms 1     # can also use num-tms to limit the number to eval
```
Or to evaluate specific TestModules, use `--selected-tms`:
```
python -m src.eval.cli evaluate <repo_name> --selected-tms GithubEnterpriseWebhookHandlerTests, TestBitbucketServerWebhookHandler
```
** Need to set your OPENAI_API_KEY

4. The evaluation step should have generated some test results, you can view them at `src/eval/output/<repo_name>`. These are yaml files show you the test files generated for each repo and the coverage improvement:
```
repo_name: codecovapi-neutered
git_hash: 2e7fd7eb7741b48214c2ab7f0be4cc721d48a2c8
tm_name: GithubEnterpriseWebhookHandlerTests
tests:
- name: GithubEnterpriseWebhookHandlerTests.test_installation_event_creates_github_app_installation
  coverage_added: 1
  code: |-
    def test_installation_event_creates_github_app_installation(self):
            owner = OwnerFactory(service="github", service_id=123456)
            self._post_event_data(
                event=GitHubWebhookEvents.INSTALLATION,
                data={
...
```
You can take a look at the tests generated before using the `apply` command to apply these patches to your target repo:
```
python -m src.eval.cli apply <output_path>         # output_path can be either the folder or a single YAML output file
```
Voila you got new tests!


## Evaluations
There is special `setup` mode which is mainly used by me for developing/benchmarking. 
```
python -m src.eval.cli setup-repo-eval <repo_name> --num-tms 1 --keep 2
```
More about this is in the docs/evaluations.txt

## Contributing
Would love to take contributions on the following:
1. Support for languages other than Python
