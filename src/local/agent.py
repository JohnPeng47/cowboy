import glob
import re
from typing import Literal, List
from dataclasses import dataclass
from jinja2 import Template

from enum import Enum
from src.llm import LLMModel

class Prompt:
    prompt = ""

    def render(self, **kwargs):
        return Template(self.prompt).render(**kwargs)


# Define size configurations in number of lines
CONTEXT_SIZES = {
    "small": 2,  # 2 lines before and after
    "med": 5,    # 5 lines before and after
    "large": 10  # 10 lines before and after
}

SizeOption = Literal["small", "med", "large"]

@dataclass
class SearchMatch:
    filename: str
    line_number: int
    match_line: str
    context_before: List[str]
    context_after: List[str]

def context_search(file_glob: str, query: str, size: SizeOption = "med") -> List[SearchMatch]:
    """
    Search for a query in files matching the glob pattern and return matches with context.
    
    Args:
        file_glob: Glob pattern for files to search
        query: Search query (treated as case-insensitive regex)
        size: Size of context window ("small", "med", "large")
    
    Returns:
        List of SearchMatch objects containing the matches and their context
    """
    context_size = CONTEXT_SIZES[size]
    matches = []
    
    # Compile regex pattern for case-insensitive search
    pattern = re.compile(query, re.IGNORECASE)
    
    # Process each file matching the glob pattern
    for filename in glob.glob(file_glob):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find matches and add context
            for i, line in enumerate(lines):
                if pattern.search(line):
                    # Calculate context window boundaries
                    start = max(0, i - context_size)
                    end = min(len(lines), i + context_size + 1)
                    
                    # Get context lines
                    context_before = lines[start:i]
                    context_after = lines[i+1:end]
                    
                    # Create match object
                    match = SearchMatch(
                        filename=filename,
                        line_number=i + 1,  # 1-based line numbering
                        match_line=line.rstrip(),
                        context_before=[l.rstrip() for l in context_before],
                        context_after=[l.rstrip() for l in context_after]
                    )
                    matches.append(match)
                    
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            
    return matches

def format_match(match: SearchMatch) -> str:
    """Format a search match with context for display."""
    lines = []
    lines.append(f"\n=== {match.filename}:{match.line_number} ===")
    
    # Add context before with line numbers
    for i, line in enumerate(match.context_before, start=match.line_number-len(match.context_before)):
        lines.append(f"{i:4d}  {line}")
    
    # Add matching line (highlighted)
    lines.append(f"{match.line_number:4d}> {match.match_line}")
    
    # Add context after with line numbers
    for i, line in enumerate(match.context_after, start=match.line_number+1):
        lines.append(f"{i:4d}  {line}")
    
    return "\n".join(lines)


# this is effectively a two-state, linear agent
class AgentState(str, Enum):
    THINKING = "THINKING"
    ACTION = "ACTION"
    OBSERVE = "OBSERVE"
    
GOAL = """You are given a unit test file. Your goal is to determine the unique sourcefile that this testfile is meant to cover. 
Here is the file: 
{test_file}
"""

class TargetSrcThinking(Prompt):
    prompt = """
{% if history %}
Here is your execution history:
{{history}}
{% endif %}

GOAL:
{{goal}}

ACTIONS:
To do so, generate a series of grep commands in the form:

(file_glob, query, small|med|large) -> where the size indicates the size of the surrounding context
to be included

Along with each grep command, give your reasoning why based on current observations. The output of your 
command will be provided to you, and you will continue taking action until you have uncovered all likely
candidates (there may be more than one) for the target source file
"""

# possible architecture here is to use a linear history that the agent coming afterwards can just
# pop items off of
class Agent:
    def __init__(self,
                 goal: str,
                 model: LLMModel,
                 use_cache: bool):
        self._goal = goal
        self._model = model
        self._use_cache = use_cache
        self._resolved = False
        
        # move this into parameters
        self._transitions = {
            AgentState.THINKING : {
                "prompt" : TargetSrcThinking(),
                "model_name": "claude", 
                "response_format": None,
                "callback": "" # ??
            },
            AgentState.OBSERVE : ""
        }
        self._current_state = AgentState.THINKING
        self._history = ""

    def run(self):
        """
        Load the prompt args
        """
        while not self._resolved or self._budget > 0:
            prompt = self._transitions[self._current_state]["prompt"]
            if self._current_state == AgentState.THINKING:
                prompt = prompt.render({
                    "history": self._history,
                    "goal": self._goal,
                })
            elif self._current_state == AgentState.OBSERVE:
                prompt = prompt.render({
                })    
                
            output = self._model.invoke(
                prompt,
                model_name      = self._transitions[self._current_state]["model_name"],
                response_format = self._transitions[self._current_state]["response_format"]
            )
        

    def transition(self, next_state: AgentState):
        self._current_state = next_state