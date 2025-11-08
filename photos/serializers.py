from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction

from .models import Photograph, Photographer, PhotoSource


class UserPublicSerializer(serializers.ModelSerializer):
    """Serializer for our custom User model."""

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "first_name", "last_name")


class PhotoSourceSerializer(serializers.ModelSerializer):
    """Serializer for a PhotoSource model."""

    class Meta:
        model = PhotoSource
        fields = (
            "id",
            "original",
            "medium",
            "small",
            "tiny",
            "large",
            "large_2x",
            "portrait",
            "landscape",
        )


class PhotographSlimSerializer(serializers.ModelSerializer):
    """
    Serializer (slim) for a Photograph model that omits the Photographer field.
    Fetches the related `source` field for PhotoSource info.
    """

    # Link in nested `source` field as writable (and not required)
    source = PhotoSourceSerializer(required=False)
    photographer_id = serializers.IntegerField(source="photographer.id", read_only=True)

    class Meta:
        model = Photograph
        fields = [
            "id",
            "title",
            "url",
            "avg_color",
            "alt_text",
            "source",
            "photographer_id",
        ]
        read_only_fields = ("id", "date_created", "last_updated", "photographer_id")


class PhotographerSerializer(serializers.ModelSerializer):
    """
    Serializer (limited) for a Photographer model that omits the photographs field.
    Fetches the related `user` field for the parent User data.
    """

    user = UserPublicSerializer(read_only=True)

    class Meta:
        model = Photographer
        fields = ["id", "user", "date_created", "last_updated"]


class PhotographSerializer(PhotographSlimSerializer):
    """
    Serializer for a Photograph model that extends the `PhotographSlimSerializer`.
    Adds an additional fetch for the related `photographer` field to include the
    link to Photographer information. Also auto-creates PhotoSource record if
    created Photograph data includes source info.
    """

    photographer = PhotographerSerializer(read_only=True)

    class Meta(PhotographSlimSerializer.Meta):
        # extend base class fields and add `photographer`
        fields = PhotographSlimSerializer.Meta.fields + [
            "photographer",
        ]

    def create(self, validated_data):
        # check for optional `source` data and auto-create PhotoSource record if defined
        source_data = validated_data.pop("source", None)
        photo = Photograph.objects.create(**validated_data)
        if source_data:
            PhotoSource.objects.create(photograph=photo, **source_data)
        return photo

    @transaction.atomic
    def update(self, instance, validated_data):
        # pull nested 'source' off the validated data
        source_data = validated_data.pop("source", None)

        # update Photograph fields in general
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        # create/update PhotoSource data, if included
        if source_data is not None:
            if src := getattr(instance, "source", None):
                for attr, val in source_data.items():
                    setattr(src, attr, val)
                src.save()
            else:
                PhotoSource.objects.create(photograph=instance, **source_data)

        return instance
