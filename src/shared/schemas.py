# src/shared/schemas.py
from pydantic import BaseModel


class WSMessage(BaseModel):
    type: str
    payload: dict
