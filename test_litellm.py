import instructor
from litellm import completion
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int


client = instructor.from_litellm(completion)


messages = [{ "content": "Hello, how are you?","role": "user"}]

# resp = client.chat.completions.create(
#     model="claude-3-5-sonnet-latest",
#     max_tokens=1024,
#     messages=[
#         {
#             "role": "user",
#             "content": "Extract Jason is 25 years old.",
#         }
#     ],
#     response_model=User,
# )
# print(resp)

# resp = client.chat.completions.create(
#     model="gpt-4o",
#     max_tokens=1024,
#     messages=[
#         {
#             "role": "user",
#             "content": "Extract Jason is 25 years old.",
#         }
#     ],
#     response_model=User,
# )
# print(resp)


# resp = client.chat.completions.create(
#     model="deepseek/deepseek-chat",
#     max_tokens=1024,
#     messages=[
#         {
#             "role": "user",
#             "content": "Extract Jason is 25 years old.",
#         }
#     ],
#     response_model=User,
# )
# print(resp)

resp = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hello?.",
        }
    ],
    response_model=None,
)