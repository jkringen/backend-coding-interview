import random
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple
from unittest.mock import patch

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

    # PHOTO_API: str = reverse("api_photo")
    """URL for photo API endpoint."""


@dataclass
class PhotoUpdateContext:
    errors: Optional[list[dict[str, str]]] = None
    response: Optional[Any] = None
    http_code: Optional[int] = None
    mock_validate_photograph: Optional[Any] = None
    mock_update_photograph: Optional[Any] = None
    post_data: Optional[Any] = None
    photo_id: Optional[Any] = None
    validated_data: Optional[Any] = None
    pre_test_setup: Optional[Callable] = None


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

        # SUT
        response: HttpResponse = self.client.get(reverse("api_healthcheck"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), expected_response)

    ##############
    # PHOTOS API #
    ##############

    @patch("api.views.get_photographs")
    def test_get_all_photos_failure(self, mock_get_photographs):
        # configures get_photos to return a failure
        # random array of "errors" / random sentences & random HTTP response code
        expected_errors: list[str] = self._random_dbresult_errors()
        expected_http_code: int = random.choice(HTTP_FAILURE_CODES)
        get_photographs_response: DbResult = DbResult(
            success=False, errors=expected_errors, http_code=expected_http_code
        )
        mock_get_photographs.return_value = get_photographs_response

        # SUT
        response: HttpResponse = self.client.get(ApiEndpoints.PHOTOS_API)

        # ensure response returned expected http code and "errors"
        self.assertEqual(response.status_code, expected_http_code)
        self.assertListEqual(response.json(), expected_errors)

    @patch("api.views.get_photographs")
    def test_get_all_photos_success(self, mock_get_photographs):
        # configures get_photographs to return a success with a randomized payload to verify
        expected_response: dict[str, str] = self.fake.pydict(allowed_types=(str,))
        mock_get_photographs.return_value = DbResult(success=True, result=expected_response)

        # SUT
        response: HttpResponse = self.client.get(ApiEndpoints.PHOTOS_API)

        # validate status code and
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), expected_response)

    @patch("api.views.validate_photograph")
    def test_post_photo_validation_failure(self, mock_validate_photograph):
        # configures validate_photograph to return a failure
        # random list of "errors" / random dictionaries
        expected_errors: list[dict[str, str]] = self._random_validation_errors()
        mock_validate_photograph.return_value = ValidatedData(success=False, errors=expected_errors, data=None)

        # SUT
        response: HttpResponse = self.client.post(
            ApiEndpoints.PHOTOS_API, self.fake.pydict(allowed_types=(str,)), format="json"
        )

        # ensure response returned expected http code and "errors"
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(response.json(), expected_errors)

    @patch("api.views.validate_photograph")
    @patch("api.views.serialize_and_save_photograph")
    def test_post_photo_serialize_save_failure(self, mock_serialize_and_save_photograph, mock_validate_photograph):
        # configures validate_photograph to return a success and serialize_and_save_photograph a failure
        # random list of "errors" / random dictionaries
        mock_validate_photograph.return_value = ValidatedData(success=True, data=None, errors=None)
        expected_errors: list[dict[str, str]] = self._random_validation_errors()
        expected_http_code: int = random.choice(HTTP_FAILURE_CODES)
        mock_serialize_and_save_photograph.return_value = DbResult(
            success=False, errors=expected_errors, http_code=expected_http_code
        )

        # SUT
        response: HttpResponse = self.client.post(
            ApiEndpoints.PHOTOS_API, self.fake.pydict(allowed_types=(str,)), format="json"
        )

        # ensure response returned expected http code and "errors"
        self.assertEqual(response.status_code, expected_http_code)
        self.assertListEqual(response.json(), expected_errors)

    @patch("api.views.validate_photograph")
    @patch("api.views.serialize_and_save_photograph")
    def test_post_photo_success(self, mock_serialize_and_save_photograph, mock_validate_photograph):
        # configures validate_photograph and serialize_and_save_photograph to return success
        # includes an expected response to verify
        expected_response: dict[str, str] = self.fake.pydict(allowed_types=(str,))
        validated_data: ValidatedData = ValidatedData(success=True, data=None, errors=None)
        mock_validate_photograph.return_value = validated_data
        mock_serialize_and_save_photograph.return_value = DbResult(success=True, result=expected_response)
        post_data: dict[str, str] = self.fake.pydict(allowed_types=(str,))

        # SUT
        response: HttpResponse = self.client.post(ApiEndpoints.PHOTOS_API, post_data, format="json")

        # ensure response returned expected 201 http code and body payload
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(response.json(), expected_response)
        mock_validate_photograph.assert_called_with(post_data)
        mock_serialize_and_save_photograph.assert_called_with(validated_data)

    #############
    # PHOTO API #
    #############

    @patch("api.views.get_photograph")
    def test_get_photo_bad_request(self, mock_get_photograph):
        # configures get_photograph to return a failure
        # random array of "errors" / random sentences & random HTTP response code
        expected_errors: list[str] = self._random_dbresult_errors()
        expected_http_code: int = random.choice(HTTP_FAILURE_CODES)
        mock_get_photograph.return_value = DbResult(success=False, errors=expected_errors, http_code=expected_http_code)
        url, _ = self._get_photo_url()

        # SUT
        response: HttpResponse = self.client.get(url)

        # ensure response returned expected 400 http code
        self.assertEqual(response.status_code, expected_http_code)
        self.assertListEqual(response.json(), expected_errors)

    @patch("api.views.get_photograph")
    def test_get_photo_success(self, mock_get_photograph):
        # configures get_photograph to return a success including a randomize expected response
        expected_response: dict[str, str] = self.fake.pydict(allowed_types=(str,))
        mock_get_photograph.return_value = DbResult(success=True, result=expected_response)
        url, photo_id = self._get_photo_url()

        # SUT
        response: HttpResponse = self.client.get(url)

        # validate status code and
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), expected_response)
        mock_get_photograph.assert_called_with(photo_id)

    @patch("api.views.update_photograph")
    @patch("api.views.validate_photograph")
    def test_update_photo_validation_failure(self, mock_validate_photograph, mock_update_photograph):
        # configures validate_photograph to return a failure with a random set of errors
        expected_errors: list[dict[str, str]] = self._random_validation_errors()
        mock_validate_photograph.return_value = ValidatedData(success=False, errors=expected_errors, data=None)

        # SUT (multiple update tests in a row)
        self._perform_photo_update_tests(
            self._assert_photo_update_failure,
            PhotoUpdateContext(errors=expected_errors, http_code=status.HTTP_400_BAD_REQUEST),
        )

    @patch("api.views.update_photograph")
    @patch("api.views.validate_photograph")
    def test_update_photo_save_failure(self, mock_validate_photograph, mock_update_photograph):
        # configures validate_photograph to return a success, but update_photograph to return a failure
        mock_validate_photograph.return_value = ValidatedData(success=True, data=None, errors=None)
        expected_errors: list[str] = self._random_dbresult_errors()
        expected_http_code: int = random.choice(HTTP_FAILURE_CODES)
        mock_update_photograph.return_value = DbResult(
            success=False, errors=expected_errors, http_code=expected_http_code
        )

        # SUT (multiple update tests in a row)
        self._perform_photo_update_tests(
            self._assert_photo_update_failure,
            PhotoUpdateContext(errors=expected_errors, http_code=expected_http_code),
        )

    @patch("api.views.update_photograph")
    @patch("api.views.validate_photograph")
    def test_update_photo_success(self, mock_validate_photograph, mock_update_photograph):
        def test_setup(context: PhotoUpdateContext):
            # re-usable setup method, configures validate_photograph and update_photograph to both return a success
            # generates random post_data and response data for validating
            context.validated_data = ValidatedData(success=True, data=None, errors=None)
            context.mock_validate_photograph.return_value = context.validated_data
            context.response = self.fake.pydict(allowed_types=(str,))
            context.mock_update_photograph.return_value = DbResult(success=True, result=context.response)
            context.post_data = self.fake.pydict(allowed_types=(str,))

        # SUT (multiple update tests in a row)
        self._perform_photo_update_tests(
            self._assert_photo_update_success,
            PhotoUpdateContext(
                http_code=status.HTTP_201_CREATED,
                mock_validate_photograph=mock_validate_photograph,
                mock_update_photograph=mock_update_photograph,
                pre_test_setup=test_setup,
            ),
        )

    def _perform_photo_update_tests(self, assertion_handler: Callable, context: PhotoUpdateContext):
        """Performs multiple update tests via multiple http methods (shared logic)."""

        def execute_test(method: str) -> HttpResponse:
            # dynamically call client http method and return response
            api_method: Callable = getattr(self.client, method, None)

            # get url and random photo_id (store photo_id in context for potential assertion)
            url, photo_id = self._get_photo_url()
            context.photo_id = photo_id

            # call api method and return response
            return api_method(url, context.post_data, format="json")

        # SUT (run test and assertions for multiple methods (logic is shared for updates))
        for method in ("put", "patch"):
            if context.pre_test_setup:
                context.pre_test_setup(context)
            response: HttpResponse = execute_test(method)
            assertion_handler(response, context)

    def _assert_photo_update_failure(self, response: HttpResponse, context: PhotoUpdateContext):
        """Helper method to assert photo update FAILURE tests."""
        # validate status code is a 400 bad request and expected errors are returned
        self.assertEqual(response.status_code, context.http_code)
        self.assertListEqual(response.json(), context.errors)

    def _assert_photo_update_success(self, response: HttpResponse, context: PhotoUpdateContext):
        """Helper method to assert photo update SUCCESS tests."""
        # validate status code is a 400 bad request and expected errors are returned
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(response.json(), context.response)
        context.mock_validate_photograph.assert_called_with(context.post_data, is_update=True)
        context.mock_update_photograph.assert_called_with(context.photo_id, context.validated_data)

    ###########
    # UTILITY #
    ###########

    def _random_dbresult_errors(self) -> list[str]:
        """Generate random list of error messages for a `DbResult` instance."""
        return self.fake.sentences(nb=self.fake.random_int(min=1, max=5))

    def _random_validation_errors(self) -> list[dict[str, str]]:
        """Generate random list of error messages for a `ValidatedData` instance."""
        return [self.fake.pydict(allowed_types=(str,)) for _ in range(self.fake.random_int(min=1, max=5))]

    def _get_photo_url(self) -> Tuple[str, int]:
        """Generates photo URL with random photo_id populated. Returns tuple (url, id)."""
        random_id: int = self.fake.random_int()
        return (reverse("api_photo", kwargs={"photo_id": random_id}), random_id)
