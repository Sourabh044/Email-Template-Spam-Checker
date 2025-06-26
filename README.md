# 📧 Email Spam Analyzer & Rewriter

This is an intelligent web-based tool that uses Google GenAI and LangChain to:

✅ Check email content for spammy or high-risk marketing language

🔁 Suggest a professionally rewritten version

🧠 Provide a list of key improvements to explain what was fixed and why

## 🚀 Features

- ✉️ Email Quality Checker
  Detects spammy phrases, assigns a spam score, and gives constructive comments.
- 🛠 Email Rewriter (Fix Spam)
  Uses GenAI to rewrite email content in a clean, non-spammy, professional format.
- 🔎 Key Improvements Analyzer
  Explains the exact changes made in the rewritten email for better understanding.

## 🧰 Tech Stack

| Layer                | Tool/Library                    |
| -------------------- | ------------------------------- |
| 🧠 LLM Engine        | Google GenAI (via LangChain)    |
| 🔗 LLM Orchestration | LangChain                       |
| ⚙️ Backend         | Flask (Python)                  |
| 🌐 Frontend          | HTML + Bootstrap 5              |
| 🧪 Prompts           | PromptTemplates from text files |

## 🛠 Installation

1. Clone the repo
```bash
git clone https://github.com/Sourabh044/Email-Template-Spam-Checker.git
cd Email-Template-Spam-Checker
```

2. Install dependencies

```bash
pip install -r requirements.txt # or uv sync
```

3. Create a .env , same format as the .sample.env and put the keys there.
4. run server

```bash
    python manage.py run server # or uv run main.py
```

## Docker

1. Command

```bash
docker compose up --build
```