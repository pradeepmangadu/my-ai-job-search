import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# response1 = client.responses.create(
#     model="gpt-6-luna",
#     input = "what is spring boot in 50 words?",    
#     )

# print("AI 1 ", response1.output_text)

# response2 = client.responses.create(
#     model="gpt-6-luna",
#     input = "what are its uses in 50 words?",
#     previous_response_id =response1.id
    
#     )

# print("AI 2 ", response2.output_text)

response1 = client.responses.create(
    model="gpt-6-luna",
    input = "what is spring boot?", 
    reasoning={ "effort": "low" }, 
    text={
    "verbosity": "low"
   }
    )

print("AI 1 ", response1.output_text)


