"""
Base Pydantic v2 Contract Model for FashXStudio
Enforces strict typing, extra fields rejection, and validation.
"""

from pydantic import BaseModel, ConfigDict


class BaseContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )
