from pydantic import BaseModel, validator
from typing import List

class TokenLookupItem(BaseModel):
    id: str
    symbol: str
    name: str

class TokenLookup(BaseModel):
    data: List[TokenLookupItem]

class SubmitToken(BaseModel):
    name: str
    symbol: str
    description: str

    @validator("symbol")
    def preprocess_symbol(cls, value: str) -> str:
        return value.upper()


class Submission(SubmitToken):
    id: int

    class Config:
        orm_mode = True
