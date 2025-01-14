from src.llm import LLMModel
from pydantic import BaseModel
import dotenv

dotenv.load_dotenv()


# ERROR HERE: stored cached content is using outdated format (str)
# NOTE: responses are already cached in model
# def test_cached_invoke():
#     POETRY = [
#         "Whispers of dawn paint the sky with golden hope.",
#         "Whispers of stars adorn the silent night's embrace.",
#         "Whispers of starlight kiss the silent sea."
#     ]

#     model = LLMModel()
#     for i in range(3):
#         res = model.invoke(
#             "Write a single line of good poetry", 
#             model_name="gpt-4o", 
#             use_cache= True, 
#             key=i,
#             delete_cache=False
#         )

#         assert res == POETRY[i]

class Joke(BaseModel):
    setup: str
    punchline: str

JOKE_PROMPT = """
Tell me a joke with a setup and a punchline
"""

def test_llm_invoke_structured_oai():
    model = LLMModel()
    joke = model.invoke(JOKE_PROMPT,
                        model_name = "gpt-4o",
                        response_format=Joke)
    
    assert joke.setup
    assert joke.punchline

def test_llm_invoke_structured_claude():
    model = LLMModel()
    joke = model.invoke(JOKE_PROMPT,
                        model_name = "claude",
                        response_format=Joke)
    
    assert joke.setup
    assert joke.punchline

def test_llm_invoke_structured_deepseek():
    model = LLMModel()
    joke = model.invoke(JOKE_PROMPT,
                        model_name = "deepseek",
                        response_format=Joke)
    
    assert joke.setup
    assert joke.punchline

