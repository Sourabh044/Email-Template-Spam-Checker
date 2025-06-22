from flask import Flask, render_template, request, jsonify
from utils import get_llm, get_parallel_chain , clean_llm_response

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
        chain = get_parallel_chain(llm)
        result = chain.invoke({"email_content": email_content})
        # print(result.keys())  # Debugging output
        response = {
            "quality_check": result["quality_check"].content,   
        }

        raw_rewritten = result.get("rewritten_email", "")
        structured_output = clean_llm_response(raw_rewritten.content)

        response["rewritten_email"] = structured_output

        return jsonify(response), 200
    except Exception as e:
        raise e
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)