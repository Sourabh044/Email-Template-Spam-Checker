from pydantic import BaseModel
from typing import List

class EmailQualityOutput(BaseModel):
    spam_score: int
    spammy_phrases: List[str]
    good_phrases: List[str]
    comments: str

class Improvement(BaseModel):
    title: str
    reason: str

class RewrittenEmailOutput(BaseModel):
    rewritten_email: str
    key_improvements: List[Improvement]