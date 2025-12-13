from openai import OpenAI
from API_keys import AI_API_KEY
client = OpenAI(api_key=AI_API_KEY)
def ask_AI(prompt, message):
    response = client.responses.create(
        model="gpt-5",
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message}
        ]
    )

    return response.output_text

def control_ask_AI(full_prompt):
    response = client.responses.create(
            model="gpt-5",
            input=f'{full_prompt}'
        )

    return response.output_text

