import os

import django

# import and ensure Django is setup/loaded first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

import csv
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from photos.models import User
from faker import Faker

from photos.models import Photograph, Photographer, PhotoSource

CSV_FILE = "photos.csv"
UserModel = get_user_model()
fake = Faker()


@dataclass
class DataRow:
    id: int
    width: int
    height: int
    url: str
    photographer: str
    photographer_url: str
    photographer_id: int
    avg_color: str
    src_original: str
    src_large2x: str
    src_large: str
    src_medium: str
    src_small: str
    src_portrait: str
    src_landscape: str
    src_tiny: str
    alt: str


def _get_csv_data() -> list[DataRow]:
    data: list[DataRow] = []
    with open(CSV_FILE, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(DataRow(**row))
    return data


def _ensure_user_record(data: DataRow) -> "User":
    """Ensures that we have a User record for user defined in photo data."""
    # need a Django user
    # need to generate a email address from the name/id
    email_addr = f"photographer.{data.photographer_id}@gmail.com"
    user_record: User = UserModel.objects.filter(email=email_addr).first()
    if not user_record:
        # random password
        password: str = secrets.token_urlsafe(15)
        # try to determine a first & last name
        name_chunks: list[str] = data.photographer.split(" ", 1)
        first_name: str = name_chunks[0].strip()
        last_name: str = name_chunks[len(name_chunks) - 1].strip() if len(name_chunks) > 1 else ""
        # create user record
        user_record: User = UserModel.objects.create_user(
            username=email_addr,
            email=email_addr,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        print(f"Created User: {email_addr} id={user_record.id} password={password}")
    return user_record


def _ensure_photographer_record(data: DataRow) -> Photographer:
    """Adds a Photographer record tied to provided User."""
    # ensure we have a base Django user
    user_record: "User" = _ensure_user_record(data)

    # return auto-created Photographer record (via post save hook on User model)
    return Photographer.objects.filter(user=user_record).first()


def _add_photograph(data: DataRow, photographer: Photographer) -> Photograph:
    """Adds a Photograph record tied to provided Photographer."""
    photograph: Photograph = Photograph.objects.create(
        **{
            "title": fake.unique.text(max_nb_chars=20),
            "url": data.url,
            "avg_color": data.avg_color,
            "alt_text": data.alt,
            "photographer": photographer,
        }
    )
    print(f"Created Photograph: id={photograph.id} {data.url}")
    return photograph


def _add_photo_source(data: DataRow, photograph: Photograph) -> PhotoSource:
    """Adds a PhotoSource record tied to provided Photograph."""
    photo_source: PhotoSource = PhotoSource.objects.create(
        **{
            "photograph": photograph,
            "original": data.src_original,
            "large_2x": data.src_large2x,
            "large": data.src_large,
            "medium": data.src_medium,
            "small": data.src_small,
            "portrait": data.src_portrait,
            "landscape": data.src_landscape,
            "tiny": data.src_landscape,
        }
    )
    print(f"Created PhotoSource: id={photo_source.id}")
    return photo_source


def run():
    csv_data: list[DataRow] = _get_csv_data()
    # insert records for each Photographer first, ignoring pre-defined IDs, but re-mapping
    for row in csv_data:
        # make sure we have a Photographer record for this user
        photographer: Photographer = _ensure_photographer_record(row)

        # add Photograph record tied to user
        photograph: Photograph = _add_photograph(row, photographer)

        # add PhotoSource record tied to photo
        _add_photo_source(row, photograph)
        print("")


if __name__ == "__main__":
    run()
