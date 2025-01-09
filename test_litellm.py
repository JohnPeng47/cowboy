# import instructor
# from litellm import completion
# from pydantic import BaseModel

# class User(BaseModel):
#     name: str
#     age: int


# client = instructor.from_litellm(completion)


# messages = [{ "content": "Hello, how are you?","role": "user"}]

# # resp = client.chat.completions.create(
# #     model="claude-3-5-sonnet-latest",
# #     max_tokens=1024,
# #     messages=[
# #         {
# #             "role": "user",
# #             "content": "Extract Jason is 25 years old.",
# #         }
# #     ],
# #     response_model=User,
# # )
# # print(resp)

# # resp = client.chat.completions.create(
# #     model="gpt-4o",
# #     max_tokens=1024,
# #     messages=[
# #         {
# #             "role": "user",
# #             "content": "Extract Jason is 25 years old.",
# #         }
# #     ],
# #     response_model=User,
# # )
# # print(resp)


# # resp = client.chat.completions.create(
# #     model="deepseek/deepseek-chat",
# #     max_tokens=1024,
# #     messages=[
# #         {
# #             "role": "user",
# #             "content": "Extract Jason is 25 years old.",
# #         }
# #     ],
# #     response_model=User,
# # )
# # print(resp)

# resp = client.chat.completions.create(
#     model="gpt-4o",
#     max_tokens=1024,
#     messages=[
#         {
#             "role": "user",
#             "content": "Hello?.",
#         }
#     ],
#     response_model=None,
# )
# print(resp)


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
                        response_format=Joke,
                        use_cache=False)
    
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



test_llm_invoke_structured_deepseek()