import os
from app.utils import load_template_from_file
from app.llm_response_schemas import EmailQualityOutput, RewrittenEmailOutput
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import PydanticOutputParser


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


def get_llm(model="gemma-3n-e4b-it", temperature=0.7, api_key=GOOGLE_API_KEY):
    """Returns Gemini-Pro LLM instance via LangChain."""
    return ChatGoogleGenerativeAI(model=model, temperature=temperature, api_key=api_key)


def create_email_quality_checker_chain(llm=None, template_path=None):
    """
    Chain that analyzes email content and gives a spamminess score (0-100),
    along with explanation.
    """
    llm = llm or get_llm()
    llm = llm.with_structured_output(EmailQualityOutput)
    parser = PydanticOutputParser(pydantic_object=EmailQualityOutput)
    if not template_path:
        template_path = os.path.join(
            "app", "prompts", "email_quality_check.txt")
    prompt = PromptTemplate(
        input_variables=["email_content"],
        template=load_template_from_file(template_path),
        partial_variables={
            "format_instructions": parser.get_format_instructions()}
    )

    return prompt | llm


def create_email_rewriter_chain(llm=None, template_path=None):
    """
    Chain that takes a spammy email and rewrites it to improve quality and reduce spam.
    """
    llm = llm or get_llm()
    llm = llm.with_structured_output(RewrittenEmailOutput)
    parser = PydanticOutputParser(pydantic_object=RewrittenEmailOutput)
    # if not template_path:
    #     template_path = os.path.join("app", "prompts", "email_rewrite.txt")
    prompt = PromptTemplate(
        input_variables=["email_content"],
        template=load_template_from_file(template_path),
        partial_variables={
            "format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm 


def get_parallel_chain(llm=None,) -> RunnableParallel:
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
