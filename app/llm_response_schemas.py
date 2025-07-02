from pydantic import BaseModel , Field
from typing import List

class EmailQualityOutput(BaseModel):
    spam_score: int = Field(description="Spamminess score of the email, ranging from 0 (not spam) to 100 (very spammy).")
    spammy_phrases: List[str] = Field(description="List of phrases in the email that contribute to its spamminess.")
    good_phrases: List[str] = Field(description="List of phrases in the email that contribute to its quality.")
    comments: str = Field(description="Comments on the overall quality of the email, including suggestions for improvement.")

class Improvement(BaseModel):
    title: str = Field(description="Title of the improvement made to the email.")
    reason: str = Field(description="Reason why this improvement was made, explaining its impact on quality and spamminess.")

class RewrittenEmailOutput(BaseModel):
    rewritten_email: str = Field(description="The rewritten email content that improves quality and reduces spamminess.")
    rewritten_subject: str = Field(description="The rewritten email subject that improves quality and reduces spamminess.")
    key_improvements: List[Improvement]