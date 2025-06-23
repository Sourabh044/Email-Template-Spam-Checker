import json
import re
import os
from llm_response_schemas import EmailQualityOutput, RewrittenEmailOutput
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import PydanticOutputParser

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


def get_llm(model="gemma-3n-e4b-it", temperature=0.7, api_key=GOOGLE_API_KEY):
    """Returns Gemini-Pro LLM instance via LangChain."""
    return ChatGoogleGenerativeAI(model=model, temperature=temperature, api_key=api_key)


def load_template_from_file(file_path: str) -> str:
    """
    Load email content from a plain text (.txt) file.

    Args:
        file_path (str): Path to the .txt file containing the email body.

    Returns:
        str: Email content as a single string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    import os

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    if not content:
        raise ValueError(f"File is empty: {file_path}")

    return content


def create_email_quality_checker_chain(llm=None):
    """
    Chain that analyzes email content and gives a spamminess score (0-100),
    along with explanation.
    """
    llm = llm or get_llm()
    parser = PydanticOutputParser(pydantic_object=EmailQualityOutput)
    prompt = PromptTemplate(
        input_variables=["email_content"],
        template=load_template_from_file(
            os.path.join("prompts", "quality_check.txt")),
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )


    return prompt | llm | parser


def create_email_rewriter_chain(llm=None):
    """
    Chain that takes a spammy email and rewrites it to improve quality and reduce spam.
    """
    llm or get_llm()
    parser = PydanticOutputParser(pydantic_object=RewrittenEmailOutput)
    prompt = PromptTemplate(
        input_variables=["email_content"],
        template=load_template_from_file(os.path.join("prompts", "email_rewrite.txt")),
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser


def get_parallel_chain(llm=None):
    """
    Create a parallel chain that runs both the quality checker and rewriter chains.
    """
    llm = llm or get_llm()
    quality_checker = create_email_quality_checker_chain(llm)
    rewriter = create_email_rewriter_chain(llm)

    return RunnableParallel(
        {
            "quality_check": quality_checker,
            "rewritten_email": rewriter,
        }
    )


def run_both_chains(email_content):
    """
    Run both the quality checker and rewriter chains in parallel.
    """
    return get_parallel_chain().invoke({"email_content": email_content})


def clean_llm_response(raw_output: str) -> dict:
    """
    Cleans and parses a potentially double-escaped JSON response from an LLM.
    """
    try:
        # Step 1: Strip newlines and whitespace
        raw_output = raw_output.strip()
        match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        # Step 2: If it looks like a double-encoded JSON string (starts/ends with quotes)
        if raw_output.startswith('"') and raw_output.endswith('"'):
            # First unescape
            raw_output = bytes(raw_output, "utf-8").decode("unicode_escape")

            # Strip outer quotes
            raw_output = raw_output[1:-1]

        # Step 3: If it includes backslash escapes or \n, \t etc., decode again
        if '\\n' in raw_output or '\\"' in raw_output:
            raw_output = bytes(raw_output, "utf-8").decode("unicode_escape")

        # Step 4: Parse final clean JSON
        return json.loads(raw_output)

    except Exception as e:
        print("❌ Failed to parse LLM output:", e)
        return {
            "rewritten_email": raw_output,
            "key_improvements": []
        }


def main():
    # Sample email (you can replace this with dynamic input)
    email_text = """
    CONGRATULATIONS!!! You’ve WON a FREE iPhone!!!
    Just click HERE to claim your prize NOW. Limited time OFFER!!!
    """
    print("\n--- Running Both Chains in Parallel ---")
    result = run_both_chains(email_text)
    print("Quality Check Result:", result["quality_check"].content)
    print("Rewritten Email:", result["rewritten_email"].content)


if __name__ == "__main__":
    main()