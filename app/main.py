from flask import Flask, render_template, request, jsonify
from chains import  get_llm , create_email_quality_checker_chain , create_email_rewriter_chain
from utils import is_html_email
from llm_response_schemas import EmailQualityOutput, RewrittenEmailOutput
from langchain_core.runnables import RunnableParallel
import os
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("homepage.html")


@app.route("/analyze-email", methods=["POST"])
def analyze_email():
    data = request.get_json()
    email_content = data.get("email_content", "").strip()

    if not email_content:
        return jsonify({"error": "email_content is required"}), 400

    try:
        llm = get_llm()

        quality_checker = create_email_quality_checker_chain(llm)

        if is_html_email(email_content):
            rewriter = create_email_rewriter_chain(llm, template_path=os.path.join("app", "prompts", "email_rewrite_html.txt"))
        else:
            rewriter = create_email_rewriter_chain(llm)

        chain = RunnableParallel(
            {
                "quality_check": quality_checker,
                "rewritten_email": rewriter,
            }
        )
        result = chain.invoke({"email_content": email_content})
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
        print('------------------------------------------ html_content:', html_content)
        if not html_content:
            return jsonify({'error': 'Missing html_content'}), 400
        llm = get_llm()
        # Your LLM logic to regenerate a clean version
        if is_html_email(html_content):
            print('here')
            rewriter = create_email_rewriter_chain(llm, template_path=os.path.join("app", "prompts", "email_rewrite_html.txt"))
        else:
            rewriter = create_email_rewriter_chain(llm)
        result:RewrittenEmailOutput = rewriter.invoke({"email_content": html_content})
        print('------------------------',result.rewritten_email)
        return jsonify({
            'rewritten_email': result.rewritten_email,
            'improvements': [im.model_dump() for im in result.key_improvements],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
