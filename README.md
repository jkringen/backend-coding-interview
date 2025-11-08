# PHOTO SERVICE - BACKEND
This project is the backend for the Photo Service application and provides a Django API server serving REDSTful APIs for querying photos, photographers, protected with JWT based authentication, etc. The service is containerized using Docker and also contains a postgres database image that is used by the application.

* post_save on User to auto-create Photographer tied to User account
* docs about seeding DB and taking note of usernames and passwords

## Later TODOs
- Proper deployment pipeline, ensuring secrets are passed securely
- Pagination and next/prev links in returned data format, if enough records to break them up
- Filtering query data via query params
- Performance Monitoring / Tracking / Event Forwarding (Datadog, Splunk, etc.)

## Quickstart

1. Install project: `poetry install`
2. Pull Docker images: `docker compose pull`
3. Launch via Docker: `docker compose up` (wait for containers to be up & `healthy`)
4. Seed database by executing seed script: `poetry run python seed_db.py`

**NOTE: Be sure to take note of the output of the seeding script, which will show you randomly generated usernames and password for Photographers, auto-created based on the seed data so we have some users to test with.** 

## Installing Project
This project was built using poetry as the python dependency management system. Make sure you have poetry installed already (version `1.8.2` or greater).

In the root project folder, run: `poetry install`

This will create a virtual environment and install and required project dependencies, etc.

## Docker Setup
Before starting up the project, it's a good idea to pull all required Docker images first: `docker compose pull`

## Launching Project
To fully launch the project, you can use this command: `docker compose up`

Once all services are up and running, you can check the status with: `docker compose ps`. All containers / services should be up and running within a minute or so and none of them should be marked as `unhealthy`.

## Architecture
### REST APIs
Django REST Framework, behind uvicorn. The `api` container defined in the `docker-compose.yml` file is the service that serve up our RESTful APIs. This is launched / hosted with `uvicorn` with a basic vertical scaling setup of 4 initial workers. The APIs are available via `http://<host>:8000/api/v1/<route>`.

#### Authentication
To allow users to authenticate with a user login to the Django authentication system, `djangorestframework-simplejwt` is installed and configured to enabled authentication.

To login and get the access / refresh tokens, the user must send a POST login request to `/api/v1/token` with a body / payload of:

```
{
    "username": "<username>>",
    "password": "<password>"
}
```

If the provided credentials are validated successfully, the API will return the access & refresh tokens at that time.

For the rest of the APIs, the client must provide the proper authentication header with the access token using the Bearer token syntax.

To also support 3rd party JWTs that could be sent from the client logging in via a 3rd party service provider (Google, GitHub, etc.), `simplejwt` has also been configured for that. In the `api/auth.py` module there is ` ExternalJWTAuthentication` class that is responsible for validating an external JWT using a shared public key, etc.

**NOTE: When a user authenticates using a 3rd party JWT, the system will still ensure that a Django User record exists for that user, for parity.**

### Database
To provide a database, a postgres container is included in the Docker Compose service stack. It is available via the `db` DNS name from within the Docker network stack.

To interface with the database, define the models/tables, and generate migrations, SQLAlchemy + alembic are in place and configured.

#### Database Models
The following models are the database models currently in place within this project:

`User` -- Represents a logged valid User within the Django system. User records may also be created for users authenticating with a 3rd party service / JWT also.

`Photographer` -- Represents a Photographer, which is based on a Django User. Photographers have a basic profile and also can own one or more `Photograph` records.

`Photograph` -- Represents a `Photograph` record, which is always owned by a single `Photographer`. The `Photograph` record has all the basic fields about that `Photograph`, minus the various different source URLs. The various source URLs are stored in a related `PhotoSource` table that is mapped to `Photograph.source`.

`PhotoSource` -- Represents a list of potential alternate source URL for a given Photograph. Each `PhotoSource` is tied exclusively to a single `Photograph`.

#### Auto-setup on Application Launch
To achieve this, for now, the Docker Compose file has been configured with a `api_pre_exec` container that acts like a "one-shot" service which launches before the API service and ensures that any pending database migrations are applied and also ensures that we have a Django superuser account.

In a full production deployment environment / scenario, this may be acheived a totally different way. Perhaps on installation of a new release, a migration would be ran via a post-upgrade/install script, etc. For this simple test application, keeping it in this "one-shot" style container was easiest.

### Files & Folders
The table below provides basic descriptions of each file in the project itself.

Repository Files / Folders:
| File               | Description                                                               |
| ------------------ | ------------------------------------------------------------------------- |
| /api               | API application that hosts the RESTful API logic.                         |
| /backend           | Main Django app folder, where primary `settings.py` and setup exists.     |
| /photos            | Photos app that houses the models and database query logic, etc.          |
| .env               | Contains environment variables, provided to app via Docker Compose.       |
| docker-compose.yml | Docker compose file used to launch backend stack.                         |
| Dockerfile         | Docker build file used to build the base image used by this application.  |
| manage.py          | Django management script.                                                 |
| pyproject.toml     | Python project metadata, including all package dependencies, etc.         |
| poetry.lock        | Poetry lock file which contains metadata for all installed packages, etc. |
| seed_db.py         | Utility script for local dev/testing to seed database with sample data.   |
<br/>

API Application (files / folders of note):
| File               | Description                                |
| ------------------ | ------------------------------------------ |
| auth.py            | API authentication configuration logic.    |
| urls.py            | URL definitions for all API routes.        |
| views.py           | View definitions for each supported route. |
<br/>

Photos Application (files / folders of note):
| File                                    | Description                                    |
| --------------------------------------- | ---------------------------------------------- |
| management/commands/ensure_superuser.py | API authentication configuration logic.        |
| admin.py                                | Admin view configuration for photos models.    |
| db.py                                   | Utility methods for querying photos db.        |
| models.py                               | Houses all DB models for photos app.           |
| serializers.py                          | Various serializers for each db model, etc.    |
| signals.py                              | Hooks to auto-create User / Photographer data. |
| validators.py                           | Pydantic validators for API data.              |
<br/>