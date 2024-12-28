from ..types import Prompt, LMModelSpec
from typing import List


gpt4_spec = LMModelSpec("gpt-4", 0.01, 8192)


class AugmentTestPrompt(Prompt):
    def __init__(self):
        prompt = """The following is a unit test case written for a code feature
{{test_code}}

Extend the unit test class to increase coverage, by appending your new code into the existing code above.
Here is the structure of your output.
On first line, write the insertion line that your new code is going to be appended to
Then on the following lines, generate the code to be inserted. Keep the indentation consistent
For example, given the following input

0. class FakeClass:
1.    def fake_method(self):
2.       pass

The following output was generated
2

    def test_fake_method(self):
        pass

Now, generate your response
"""

        super().__init__(prompt, gpt4_spec, ["test_code"])


class AugmentTestPromptWithCtxt(Prompt):
    def __init__(self):
        prompt = """The following is a unit test case written for a code feature. 
{{test_code}}

{% if file_contents %}
Here is the source code file that the test intends to cover:
{{file_contents}}
{% endif %}

Extend the unit test class to increase coverage, by appending your new code into the existing code above.
Make sure that the indentation is consistent. Do not generate anything other than the new tests. Here is an example of
your output response:

def test_function1(self):
    assert cond1 == True

def test_function2(self):
    assert cond2 == False

Now, generate your response. 
"""
        super().__init__(prompt, gpt4_spec, ["test_code", "file_contents"])

# ONLY 3 RESPONSES
# class AugmentTestPromptWithCtxt(Prompt):
#     def __init__(self):
#         prompt = """The following is a unit test case written for a code feature. 
# {{test_code}}

# {% if file_contents %}
# Here is the source code file that the test intends to cover:
# {{file_contents}}
# {% endif %}

# Extend the unit test class to increase coverage, by appending your new code into the existing code above.
# Here is the structure of your output.
# On first line, write the insertion line that your new code is going to be appended to
# Then on the following lines, generate the code to be inserted. Keep the indentation consistent
# For example, given the following input

# 0. class FakeClass:
# 1.    def fake_method(self):
# 2.       pass

# The following output was generated
# 2

#     def test_fake_method(self):
#         pass

# Now, generate your response. ONLY GENERATE 5 TEST CASES. ANYMORE AND SOMETHING BAD WILL HAPPEN
# """
#         super().__init__(prompt, gpt4_spec, ["test_code", "file_contents"])



class AugmentTestPromptMiss(Prompt):
    def __init__(self):
        prompt = """The following is a unit test case written for a code feature. 
{{test_code}}

{% if file_contents %}
Here is the source code file that the test intends to cover:
{{file_contents}}
{% endif %}

{% if missing_lines %}
Here are the missing lines that the augmented test should cover:
{{missing_lines}}
{% endif %}

Extend the unit test class to increase coverage, by appending your new code into the existing code above.
Here is the structure of your output.
On first line, write the insertion line that your new code is going to be appended to
Then on the following lines, generate the code to be inserted. Keep the indentation consistent
For example, given the following input

0. class FakeClass:
1.    def fake_method(self):
2.       pass

The following output was generated
2

    def test_fake_method(self):
        pass

Now, generate your response
"""
        super().__init__(
            prompt, gpt4_spec, ["test_code", "file_contents", "missing_lines"]
        )
