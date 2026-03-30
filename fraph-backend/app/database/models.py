from pydantic import BaseModel


class DatasetRecord(BaseModel):
    name: str
    path: str
