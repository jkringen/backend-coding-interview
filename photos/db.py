from dataclasses import dataclass, field
from typing import Any, Optional, Type, TypeVar

from django.db.models import Model, QuerySet
from rest_framework.serializers import ModelSerializer
from rest_framework import status

from photos.models import Photograph, Photographer
from photos.serializers import PhotographSerializer, PhotographSlimSerializer, PhotographerSerializer
from photos.validators import ValidatedData


M = TypeVar("M", bound=Model)
"""Represents a generic type for a Django Model, used to genericize types for QuerySet."""


@dataclass
class DbResult:
    """
    Represents a result of one of the operation functions in this module.
    If `success` is True, `result` should be populate with the result of the operation.
    If `success` is False, `errors` will be populate with the error(s) from the operation.
    If an error occurred, `http_code` will be set to the HTTP error code to return.
    """

    success: bool
    result: Optional[Any] = None
    errors: Optional[list[Any]] = None
    http_code: Optional[int] = field(default_factory=lambda: status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_photographers() -> DbResult:
    """Returns a list of all Photographer records."""
    queryset: QuerySet[M] = Photographer.objects.all().select_related("user")
    serializer: PhotographerSerializer = PhotographerSerializer(queryset, many=True)
    return DbResult(success=True, result=serializer.data)


def get_photographer(id: int) -> DbResult:
    """Returns Photographer record with ID matching provided `id`."""
    # find Photographer by ID, return 404 if not found
    photographer: Photographer = Photographer.objects.filter(id=id).select_related("user").first()
    if not photographer:
        return DbResult(success=False, http_code=status.HTTP_404_NOT_FOUND)

    # return serialized Photographer data
    serializer: PhotographerSerializer = PhotographerSerializer(photographer)
    return DbResult(success=True, result=serializer.data)


def get_photographs(photographer_id: Optional[int] = None, prefetch_photographer: Optional[bool] = False) -> DbResult:
    """
    Returns list of Photograph records, optionally filtered by `photographer_id`.
    If `prefetch_photographer` is True, the `photographer` field will be fetched and populated.
    """
    # build initial queryset (optionally filtering on photographer_id)
    queryset: QuerySet[M] = (
        Photograph.objects.filter(photographer_id=photographer_id).all()
        if photographer_id
        else Photograph.objects.all()
    )

    # instantiate full or limited serializer and returned serialized result
    serializer: Type[ModelSerializer] = _get_photograph_serializer(
        queryset, many=True, prefetch_photographer=prefetch_photographer
    )
    return DbResult(success=True, result=serializer.data)


def get_photograph(id: int, prefetch_photographer: Optional[bool] = False) -> DbResult:
    """
    Returns a specific Photograph record that has an ID matching `photo_id`.
    If `prefetch_photographer` is True, the `photographer` field will be fetched and populated.
    """
    # get photograph record by ID, return 404 if not found
    photograph: Photograph = Photograph.objects.filter(id=id).first()
    if not photograph:
        return DbResult(success=False, http_code=status.HTTP_404_NOT_FOUND)

    # return serialized Photograph data
    serializer: Type[ModelSerializer] = _get_photograph_serializer(
        photograph, prefetch_photographer=prefetch_photographer
    )
    return DbResult(success=True, result=serializer.data)


def update_photograph(photo_id: int, validated_data: ValidatedData) -> DbResult:
    """
    Updates an existing Photograph with provided `validated_data`.
    """
    # find existing photograph by ID, return 404 if not found
    photograph: Photograph = Photograph.objects.select_related("source").filter(id=photo_id).first()
    if not photograph:
        return DbResult(success=False, http_code=status.HTTP_404_NOT_FOUND)

    # serialize data, return error if serializer did not validate the data
    update_data = validated_data.data.model_dump(exclude_unset=True, exclude_none=True)
    serializer = PhotographSerializer(instance=photograph, data=update_data, partial=True)
    if not serializer.is_valid():
        return DbResult(success=False, errors=serializer.errors)

    # save via serializer and return success
    updated_photo = serializer.save()
    return DbResult(success=True, result=PhotographSerializer(updated_photo).data)


def serialize_and_save_photograph(validated_data: ValidatedData) -> DbResult:
    """Serializes and saves provided validated Photograph data."""
    # serialize data, return error if serializer did not validate the data
    serializer = PhotographSerializer(data=validated_data.data.model_dump())
    if not serializer.is_valid():
        return DbResult(success=False, errors=serializer.errors)

    # find Photographer record to link with photo, return 400 error if not found
    photographer = Photographer.objects.filter(id=validated_data.data.photographer_id).first()
    if not photographer:
        return DbResult(success=False, http_code=status.HTTP_400_BAD_REQUEST)

    # save to database and return success respone
    serializer.save(photographer=photographer)
    return DbResult(success=True, result=serializer.data)


def _get_photograph_serializer(
    queryset: QuerySet[M],
    prefetch_photographer: Optional[bool] = False,
    many: Optional[bool] = False,
) -> Type[ModelSerializer]:
    """Returns a full or limimted Photograph serializer (depending on `prefetch_photographer`)."""
    # if we need to prefetch Photographer, add that to the queryset now
    if prefetch_photographer:
        queryset = queryset.select_related("photographer")

    # construct full/limited serializer and return it
    SerializerCls: Type[ModelSerializer] = PhotographSerializer if prefetch_photographer else PhotographSlimSerializer
    return SerializerCls(queryset, many=many)
