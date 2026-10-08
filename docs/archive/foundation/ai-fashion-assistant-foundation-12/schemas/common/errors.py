from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=1000)
    field: str | None = Field(default=None, max_length=200)


class ErrorResponse(BaseModel):
    error: ErrorBody
