from flask import Flask, render_template, request, jsonify
from app.chains import  get_llm , create_email_quality_checker_chain , create_email_rewriter_chain
from app.utils import is_html_email
from app.llm_response_schemas import EmailQualityOutput, RewrittenEmailOutput
from langchain_core.runnables import RunnableParallel
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import os

load_dotenv()
memory = ConversationBufferMemory(return_messages=True)

app = Flask(__name__)
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-pro")  # Default to gemini-2.5-flash if not set
EMAIL_QUALITY_CHECK_PROMPT = os.environ.get("EMAIL_QUALITY_CHECK_PROMPT", "app/prompts/email_quality_check.txt")  # Default path for email quality check prompt
EMAIL_REWRITE_HTML_PROMPT = os.environ.get("EMAIL_REWRITE_HTML_PROMPT", "app/prompts/email_rewrite_html.txt")  # Default path for email rewrite prompt
EMAIL_REWRITE_TEXT_PROMPT = os.environ.get("EMAIL_REWRITE_TEXT_PROMPT", "app/prompts/email_rewrite.txt")  # Default path for email rewrite prompt

@app.route("/")
def home():
    return render_template("homepage.html")


@app.route("/analyze-email", methods=["POST"])
def analyze_email():
    data = request.get_json()
    email_content = data.get("email_content", "").strip()
    email_subject = data.get("email_subject", "").strip()
    
    if not email_content:
        return jsonify({"error": "email_content is required"}), 400

    try:
        llm = get_llm(model=LLM_MODEL,temperature=0.0)
        quality_checker = create_email_quality_checker_chain(llm,template_path=EMAIL_QUALITY_CHECK_PROMPT)

        if is_html_email(email_content):
            rewriter = create_email_rewriter_chain(llm=llm,template_path=EMAIL_REWRITE_HTML_PROMPT)
        else:
            rewriter = create_email_rewriter_chain(llm=llm,template_path=EMAIL_REWRITE_TEXT_PROMPT)

        chain = RunnableParallel(
            {
                "quality_check": quality_checker,
                "rewritten_email": rewriter,
            }
        )
        result = chain.invoke({"email_content": email_content,"email_subject":email_subject})
        # print(result)  # Debugging output

        raw_quality_check: EmailQualityOutput | str = result.get("quality_check", "")
        raw_rewritten: RewrittenEmailOutput | str = result.get("rewritten_email", "")

        response = {
            "quality_check": raw_quality_check.model_dump_json(),
            "rewritten_email": raw_rewritten.model_dump_json()
        }

        return jsonify(response), 200
    except Exception as e:
        # raise e
        return jsonify({"error": str(e)}), 500


@app.route('/regenerate-email', methods=['POST'])
def regenerate_email():
    try:
        data = request.get_json()
        html_content = data.get('html_content')
        # print('------------------------------------------ html_content:', html_content)
        if not html_content:
            return jsonify({'error': 'Missing html_content'}), 400
        llm = get_llm(model=LLM_MODEL)
        # Your LLM logic to regenerate a clean version
        if is_html_email(html_content):
            rewriter = create_email_rewriter_chain(llm=llm,template_path=EMAIL_REWRITE_HTML_PROMPT)
        else:
            rewriter = create_email_rewriter_chain(llm=llm,template_path=EMAIL_REWRITE_TEXT_PROMPT)
        result:RewrittenEmailOutput = rewriter.invoke({"email_content": html_content})
        # print('------------------------',result.rewritten_email)
        return jsonify({
            'rewritten_email': result.rewritten_email,
            'improvements': [im.model_dump() for im in result.key_improvements],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
