from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import  HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from app.chains import get_llm, create_email_quality_checker_chain, create_email_rewriter_chain , create_email_chat_chain
from app.utils import is_html_email , extract_text_from_html_email
from app.llm_response_schemas import EmailQualityOutput, RewrittenEmailOutput ,ChatRequest
from langchain_core.runnables import RunnableParallel
from langchain.memory import ConversationBufferMemory
from fastapi.staticfiles import StaticFiles
import os

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI()
# Mount static files inside the app directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates inside the app directory
templates = Jinja2Templates(directory="app/templates")

# Memory and config
memory = ConversationBufferMemory(return_messages=True)

LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-pro")
EMAIL_QUALITY_CHECK_PROMPT = os.environ.get("EMAIL_QUALITY_CHECK_PROMPT", "app/prompts/email_quality_check.txt")
EMAIL_REWRITE_HTML_PROMPT = os.environ.get("EMAIL_REWRITE_HTML_PROMPT", "app/prompts/email_rewrite_html.txt")
EMAIL_REWRITE_TEXT_PROMPT = os.environ.get("EMAIL_REWRITE_TEXT_PROMPT", "app/prompts/email_rewrite.txt")

# Request Schemas
class AnalyzeEmailRequest(BaseModel):
    email_content: str
    email_subject: str = ""

class RegenerateEmailRequest(BaseModel):
    html_content: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})

@app.post("/analyze-email")
async def analyze_email(payload: AnalyzeEmailRequest):
    email_content = payload.email_content.strip()
    email_subject = payload.email_subject.strip()

    if not email_content:
        raise HTTPException(status_code=400, detail="email_content is required")

    try:
        llm = get_llm(model=LLM_MODEL, temperature=0.0)
        quality_checker = create_email_quality_checker_chain(llm, template_path=EMAIL_QUALITY_CHECK_PROMPT)

        rewriter = create_email_rewriter_chain(
            llm=llm,
            template_path=EMAIL_REWRITE_HTML_PROMPT if is_html_email(email_content) else EMAIL_REWRITE_TEXT_PROMPT
        )

        chain = RunnableParallel({
            "quality_check": quality_checker,
            "rewritten_email": rewriter,
        })

        result = chain.invoke({
            "email_content": email_content,
            "email_subject": email_subject
        })

        raw_quality_check: EmailQualityOutput | str = result.get("quality_check", "")
        raw_rewritten: RewrittenEmailOutput | str = result.get("rewritten_email", "")

        return {
            "quality_check": raw_quality_check.model_dump_json(),
            "rewritten_email": raw_rewritten.model_dump_json()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/regenerate-email")
async def regenerate_email(payload: RegenerateEmailRequest):
    html_content = payload.html_content.strip()

    if not html_content:
        raise HTTPException(status_code=400, detail="Missing html_content")

    try:
        llm = get_llm(model=LLM_MODEL)
        rewriter = create_email_rewriter_chain(
            llm=llm,
            template_path=EMAIL_REWRITE_HTML_PROMPT if is_html_email(html_content) else EMAIL_REWRITE_TEXT_PROMPT
        )

        result: RewrittenEmailOutput = rewriter.invoke({"email_content": html_content})

        return {
            "rewritten_email": result.rewritten_email,
            "improvements": [im.model_dump() for im in result.key_improvements]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-email-helper")
async def chat_email_helper(payload: ChatRequest):
    try:
        llm = get_llm(model=LLM_MODEL)
        email_content = payload.email_content
        if is_html_email(email_content):
            email_content = extract_text_from_html_email(email_content)
        
        print(email_content)
        chain = create_email_chat_chain(llm)
        response = chain.invoke({"question": payload.question,"email_content": email_content})
        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))