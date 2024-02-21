"""
Purpose:
    Interact with the GENAI API.
    Provide supporting prompt engineering functions.
"""

import re
import sys
from dotenv import load_dotenv
import os
from typing import Any, Dict
# import openai
from genai import Client, Credentials
import genai
from genai.extensions.llama_index import IBMGenAILlamaIndex
from genai.schema import DecodingMethod, TextGenerationParameters
from llama_index.llms.base import ChatMessage
from llama_index.llms.types import MessageRole
# from genai.extensions.langchain import LangChainInterface


# load .env file
load_dotenv()

# assert os.environ.get("GENAI_API_KEY")
# assert os.environ.get("API_BASE")

# get BAM api key
GENAI_KEY="GENAI KEY"
GENAI_API="https://bam-api.res.ibm.com"

# genai.api_key = os.environ.get("GENAI_API_KEY")


# ------------------ helpers ------------------

def extract_text_between_strings(input_text, start_string, end_string):
    pattern = re.compile(f'{re.escape(start_string)}(.*?){re.escape(end_string)}', re.DOTALL)
    # pattern = "```sql(.*?)```"
    # pattern = re.compile(f'{re.escape(start_string)}(.*?)(?=(?:\bSELECT\b|\bFROM\b|$))', re.DOTALL | re.IGNORECASE)
    # pattern = re.compile(f'{re.escape(start_string)}(.*?)(?=(?<!\\\\);\s*\n)', re.DOTALL | re.IGNORECASE)
    match = pattern.search(input_text)

    if match:
        return match.group(1).strip()
    else:
        return None

# ------------------ content generators ------------------


def prompt(prompt: str, model: str = "meta-llama/llama-2-70b-chat") -> str:
    # validate the openai api key - if it's not valid, raise an error
    if not GENAI_KEY:
        sys.exit(
            """
ERORR: BAM API key not found. Please export your key to GENAI_KEY
Example bash command:
    export GENAI_KEY=<your BAM apikey>
            """
        )
    # client = openai.OpenAI()
    credentials = Credentials(api_key=GENAI_KEY,api_endpoint=GENAI_API)
    client = Client(credentials=credentials)
    llm = IBMGenAILlamaIndex(
        client=client,
        model_id=model,
        parameters=TextGenerationParameters(
            decoding_method="greedy",
            max_new_tokens=125,
            min_new_tokens=10,
            temperature=0.1,
            top_k=50,
            top_p=1,
        ),
    )
    message=llm.chat(
        messages=[
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=prompt,
            ),
            ChatMessage(role=MessageRole.USER, content=prompt),
        ],
    )
    response=message.__str__()
    print(extract_text_between_strings(response,"<sql query exclusively as raw text>","</sql query>"))
    return response


def add_cap_ref(
    prompt: str, prompt_suffix: str, cap_ref: str, cap_ref_content: str
) -> str:
    """
    Attaches a capitalized reference to the prompt.
    Example
        prompt = 'Refactor this code.'
        prompt_suffix = 'Make it more readable using this EXAMPLE.'
        cap_ref = 'EXAMPLE'
        cap_ref_content = 'def foo():\n    return True'
        returns 'Refactor this code. Make it more readable using this EXAMPLE.\n\nEXAMPLE\n\ndef foo():\n    return True'
    """

    new_prompt = f"""{prompt} {prompt_suffix}\n\n{cap_ref}\n\n{cap_ref_content}"""
    
    return new_prompt
