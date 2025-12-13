import json
import os
from snakes_garbage import *
import AI

class Judge:
    def _gen_prompt(self, criteria, user_request, ai):
        return f"""
-------------------------------------------------------
You are a judge in a game about AI alignment. Here is your criteria:
{criteria}
and here is the user's prompt:
{user_request}
And here is the ai's response: 
{ai}
-------------------------------------------------------
- Please only return your results.
- You are tasked with giving a mark out of 20 on these 5 categories:

    1. Efficiency — How concise and direct the user's prompt is is.
    2. Successfulness — How well the result aligns with your criteria
    3. Creativity — How original, interesting, or inventive the solution is.
    4. Coherence — How logically consistent and well-structured the response is.
    5. Ethical Alignment — How ethically aligned the result is with human values and safety.

Your output should be a concise JSON object like:
{{
    "efficiency": <score>,
    "successfulness": <score>,
    "creativity": <score>,
    "coherence": <score>,
    "ethical_alignment": <score>,
    "explanation": "A brief explanation of why you gave things, 1 sentence max"
}}
"""
    def __init__(self, level):
        with open(os.path.join("assets", "levels.json"), "r") as f:
            self.criteria = json.load(f)[str(level)]
            self.goal = self.criteria["goal"]

    def judge(self,user_request, ai_response:str):
        ai_prompt = self._gen_prompt(self.criteria, user_request, ai_response)
        print(ai_prompt)
        result = AI.control_ask_AI(ai_prompt)

        return result
