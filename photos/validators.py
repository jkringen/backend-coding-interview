from dataclasses import dataclass
from typing import Annotated, Any, Optional
import logging

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    ValidationError,
)

logger = logging.getLogger(__name__)

NameField = Annotated[str, StringConstraints(max_length=50)]
"""Provides constraints for a str field representing a name."""


class PhotoSourceValidator(BaseModel):
    """Validator for PhotoSource payloads."""

    model_config = ConfigDict(extra="forbid")
    original: Optional[str] = None
    medium: Optional[str] = None
    small: Optional[str] = None
    tiny: Optional[str] = None
    large: Optional[str] = None
    large_2x: Optional[str] = None
    portrait: Optional[str] = None
    landscape: Optional[str] = None


class PhotographValidator(BaseModel):
    """Validator for creating a new Photograph record."""

    model_config = ConfigDict(extra="forbid")
    title: str
    url: str
    source: PhotoSourceValidator
    avg_color: Optional[str] = None
    alt_text: Optional[str] = None


class PhotographUpdateValidator(BaseModel):
    """Validator used for updating a Photograph record."""

    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = None
    url: Optional[str] = None
    source: Optional[PhotoSourceValidator] = None
    avg_color: Optional[str] = None
    alt_text: Optional[str] = None


@dataclass
class ValidatedData:
    """
    Holds the result of a data validation.
    If `success` is True, the `data` property will contain the validated data.
    If `success` is False, the `data` property will be null and `errors` will be populated.
    """

    data: BaseModel | None
    success: bool
    errors: list[dict[str, Any]] | None


def validate_photograph(data: dict[str, Any], is_update: Optional[bool] = False) -> ValidatedData:
    """Validates incoming new Photograph data and returns the result."""
    validated_data: BaseModel | None = None
    errors: list[dict[str, Any]] | None = None
    try:
        validated_data = PhotographUpdateValidator(**data) if is_update else PhotographValidator(**data)
    except ValidationError as e:
        errors = e.errors()
        logger.error(f"Photograph valdation FAILURE: errors={errors}")
    return ValidatedData(
        **{
            "data": validated_data,
            "success": True if errors is None else False,
            "errors": errors,
        }
    )
