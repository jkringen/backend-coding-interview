from typing import Any, Tuple
from unittest.mock import patch
import random

import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.http import HttpResponse
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from photos.db import DbResult
from photos.validators import ValidatedData

User = get_user_model()

HTTP_FAILURE_CODES: Tuple[int] = (
    status.HTTP_400_BAD_REQUEST,
    status.HTTP_401_UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_404_NOT_FOUND,
    status.HTTP_500_INTERNAL_SERVER_ERROR,
    status.HTTP_405_METHOD_NOT_ALLOWED,
    status.HTTP_406_NOT_ACCEPTABLE,
)
"""List of HTTP `failure` codes to use in randomized values."""


class ApiEndpoints:
    PHOTOS_API: str = reverse("api_photos")
    """URL for photos API endpoint."""


class APITestCaseWithJWT(APITestCase):
    fake: Faker
    user: AbstractUser
    access_token: str

    def setUp(self):
        # setup faker
        self.fake = Faker()

        # enable full diffs
        self.maxDiff = None

        # create user for test session
        user_password: str = self.fake.password()
        username: str = self.fake.user_name()
        user_email: str = self.fake.email()
        self.user = User.objects.create_user(username=username, email=user_email, password=user_password)

        # Obtain a token
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"username": username, "password": user_password}, format="json")
        self.access_token = response.data["access"]

        # Set the authorization header for our protected routes
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_healthcheck(self):
        expected_response: dict[str, Any] = {"status": "healthy"}

        response: HttpResponse = self.client.get(reverse("api_healthcheck"))  # SUT

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), expected_response)

    @patch("api.views.get_photographs")
    def test_get_all_photos_failure(self, mock_get_photographs):
        # setup mock_get_photos to simulate a failure
        # random array of "errors" / random sentences & random HTTP response code
        expected_errors: list[str] = self.fake.sentences(nb=self.fake.random_int(min=1, max=5))
        expected_http_code: int = random.choice(HTTP_FAILURE_CODES)
        get_photographs_response: DbResult = DbResult(
            success=False, errors=expected_errors, http_code=expected_http_code
        )
        mock_get_photographs.return_value = get_photographs_response

        response: HttpResponse = self.client.get(ApiEndpoints.PHOTOS_API)  # SUT

        # ensure response returned expected http code and "errors"
        self.assertEqual(response.status_code, expected_http_code)
        self.assertListEqual(response.json(), expected_errors)

    @patch("api.views.get_photographs")
    def test_get_all_photos_success(self, mock_get_photographs):
        # generate a random dictionary to return from mock get_photoghaphs, mark as success result
        expected_response: dict[str, str] = self.fake.pydict(allowed_types=(str,))
        mock_get_photographs.return_value = DbResult(success=True, result=expected_response)

        response: HttpResponse = self.client.get(ApiEndpoints.PHOTOS_API)  # SUT

        # validate status code and
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), expected_response)

    @patch("api.views.validate_photograph")
    def test_post_photo_validation_failure(self, mock_validate_photograph):
        # setup mock_validate_photograph to simulate a failure
        # random list of "errors" / random dictionaries
        expected_errors: list[dict[str, str]] = [
            self.fake.pydict(allowed_types=(str,)) for _ in range(self.fake.random_int(min=1, max=5))
        ]
        mock_validate_photograph.return_value = ValidatedData(success=False, errors=expected_errors, data=None)

        response: HttpResponse = self.client.post(
            ApiEndpoints.PHOTOS_API, self.fake.pydict(allowed_types=(str,))
        )  # SUT

        # ensure response returned expected http code and "errors"
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(response.json(), expected_errors)

    @patch("api.views.validate_photograph")
    @patch("api.views.serialize_and_save_photograph")
    def test_post_photo_serialize_save_failure(self, mock_serialize_and_save_photograph, mock_validate_photograph):
        # setup mock_validate_photograph to report a success
        # setup mock_serialize_and_save_photograph to simulate a failure
        # random list of "errors" / random dictionaries
        mock_validate_photograph.return_value = ValidatedData(success=True, data=None, errors=None)
        expected_errors: list[dict[str, str]] = [
            self.fake.pydict(allowed_types=(str,)) for _ in range(self.fake.random_int(min=1, max=5))
        ]
        expected_http_code: int = random.choice(HTTP_FAILURE_CODES)
        mock_serialize_and_save_photograph.return_value = DbResult(
            success=False, errors=expected_errors, http_code=expected_http_code
        )

        response: HttpResponse = self.client.post(
            ApiEndpoints.PHOTOS_API, self.fake.pydict(allowed_types=(str,))
        )  # SUT

        # ensure response returned expected http code and "errors"
        self.assertEqual(response.status_code, expected_http_code)
        self.assertListEqual(response.json(), expected_errors)

    @patch("api.views.validate_photograph")
    @patch("api.views.serialize_and_save_photograph")
    def test_post_photo_success(self, mock_serialize_and_save_photograph, mock_validate_photograph):
        # setup all mocks to report a success and a fake expected return payload
        expected_response: dict[str, str] = self.fake.pydict(allowed_types=(str,))
        mock_validate_photograph.return_value = ValidatedData(success=True, data=None, errors=None)
        mock_serialize_and_save_photograph.return_value = DbResult(success=True, result=expected_response)

        response: HttpResponse = self.client.post(
            ApiEndpoints.PHOTOS_API, self.fake.pydict(allowed_types=(str,))
        )  # SUT

        # ensure response returned expected 201 http code and body payload
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(response.json(), expected_response)
