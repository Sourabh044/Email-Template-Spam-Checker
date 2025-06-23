import json
import re
from bs4 import BeautifulSoup


def is_html_email(content: str) -> bool:
    return bool(BeautifulSoup(content, "html.parser").find()) and "<html" in content.lower()


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
