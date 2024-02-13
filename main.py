import os
from utlities.sqlite import SQLiteManager
from utlities import llm_BAM
import dotenv
import argparse

dotenv.load_dotenv()

# assert os.environ.get("DB_URL"), "SQLITE_CONNECTION_URL not found in .env file"
# assert os.environ.get(
#     "BAM_API_KEY"
# ), "BAM_API_KEY not found in .env file"

# DB_URL = os.environ.get("DB_URL")
DB_URL = "sqlite-agent-with-autogen\chinook.db"
# BAM_API_KEY = os.environ.get("BAM_API_KEY")

SQLITE_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"

SQL_DELIMITER = "---------"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="The prompt for the AI")
    args = parser.parse_args()
    # args.prompt=input("Enter the prompt: ")
    args.prompt="How many customers are there?"
    # args.prompt="How many albumns are created by each artist?"
    
    if not args.prompt:
        print("Please provide a prompt")
        return

    prompt = f"Fulfill this database query: {args.prompt}. "

    with SQLiteManager() as db:
        db.connect_with_url(DB_URL)

        table_definitions = db.get_table_definitions_for_prompt()

        prompt = llm_BAM.add_cap_ref(
            prompt,
            f"Use these {SQLITE_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.",
            SQLITE_TABLE_DEFINITIONS_CAP_REF,
            table_definitions,
        )

        prompt = llm_BAM.add_cap_ref(
            prompt,
            f"\n\nRespond in this format {RESPONSE_FORMAT_CAP_REF}. Replace the text between <> with it's request. I need to be able to easily parse the sql query from your response.",
            RESPONSE_FORMAT_CAP_REF,
            f"""<sql query exclusively as raw text>
{SQL_DELIMITER}
<explanation of the sql query>
""",
        )
#         prompt = llm_BAM.add_cap_ref(
#             prompt,
#             f"Generate a response in the following format: {RESPONSE_FORMAT_CAP_REF}. Replace the text between <> with its corresponding content. No explanation should be there after <sql query exclusively as raw text> only the sql command. The goal is to facilitate easy parsing of the SQL query from your response.",
#             RESPONSE_FORMAT_CAP_REF,
#             f"""<explanation of the SQL query>
# {SQL_DELIMITER}
# <sql query exclusively as raw text>
# """,
#         )
        
        print("\n\n-------- PROMPT --------")
        print(prompt)

        prompt_response = llm_BAM.prompt(prompt=prompt, model="meta-llama/llama-2-70b-chat")

        print("\n\n-------- PROMPT RESPONSE --------")
        print(prompt_response)

        sql_query = llm_BAM.extract_text_between_strings(prompt_response,"<sql query exclusively as raw text>","</sql query>")

        print(f"\n\n-------- PARSED SQL QUERY --------")
        print(sql_query)

        result = db.run_sql(sql_query)

        print("\n\n======== POSTGRES DATA ANALYTICS AI AGENT RESPONSE ========")

        print(result)


if __name__ == "__main__":
    main()