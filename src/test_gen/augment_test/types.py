from dataclasses import dataclass
from collections import defaultdict
from jinja2 import Template

from typing import List, NamedTuple
import tiktoken

from enum import Enum, auto


class StratResult(NamedTuple):
    contents: str
    test_path: str


class StrategyInitError(Exception):
    pass


class StrategyMode(Enum):
    GEN_NEW_TEST = auto()
    AUGMENT_TEST = auto()


@dataclass
class LMModelSpec:
    model: str
    cost: float
    ctxt_window: int


class CtxtWindowExceeded(Exception):
    pass


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class Prompt:
    def __init__(self, prompt: str, keywords: List[str], max_len: int = 8096):
        """
        Prompt class that is initialized with a set of key/value pairs, which can then be overriden
        via update_line to dynamically include a set of values mapped to keys
        
        Also contains utility methods for ensuring that prompt does not exceed size limits
        """
        self._prompt = prompt
        self._keyword_dict = defaultdict(lambda: "")
        self._keywords = keywords
        self._max_len = max_len
        self._current_len = self._tokenize(prompt)

    def _tokenize(self, prompt: str):
        # Fails with: ValueError: Unknown encoding <Encoding 'cl100k_base'>
        # encoding = tiktoken.encoding_for_model(self._model_name)
        return num_tokens_from_string(prompt, "cl100k_base")

    def _check_token_length(self, line: str) -> bool:
        """
        Checks if adding the line would exceed the maximum token length.
        Returns True if line can be added, False otherwise.
        """
        str_len = self._tokenize(line)
        return self._current_len + str_len <= self._max_len

    def insert_line(self, keyword: str, line: str, preamble: str = "") -> bool:
        if keyword not in self._keywords:
            raise ValueError(f"Keyword {keyword} not found in prompt")

        if not self._check_token_length(line):
            return False
        
        self._keyword_dict[keyword] += preamble + "\n" + line + "\n"
        return True
    
    def update_line(self, keyword: str, line: str, preamble: str = "") -> bool:
        """
        Updates the content for a keyword, replacing existing content.
        Returns True if update successful, False if token limit would be exceeded.
        """
        if keyword not in self._keywords:
            raise ValueError(f"Keyword {keyword} not found in prompt")
            
        if not self._check_token_length(line):
            return False
            
        self._keyword_dict[keyword] = preamble + "\n" + line + "\n"
        return True

    def get_prompt(self) -> str:
        template = Template(self._prompt)
        return template.render(**self._keyword_dict)
