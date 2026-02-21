from pydantic import BaseModel

class AnalysisCreate(BaseModel):
    question: str