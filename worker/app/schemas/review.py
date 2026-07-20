from pydantic import BaseModel


class FieldEdit(BaseModel):
    value: float | str | None
    unit: str | None = None


class ReviewRequest(BaseModel):
    edits: dict[str, FieldEdit] = {}
    approve: bool = False
