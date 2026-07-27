import asyncio
from dataclasses import dataclass

import requests
from cachecontrol import CacheControl
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import settings


class GoogleAuthNotConfiguredError(Exception):
    pass


class InvalidGoogleCredentialError(Exception):
    pass


@dataclass(frozen=True)
class GoogleIdentity:
    email: str
    subject: str


_google_request = google_requests.Request(session=CacheControl(requests.Session()))
_verification_semaphore = asyncio.Semaphore(settings.GOOGLE_VERIFICATION_MAX_CONCURRENCY)


async def verify_google_credential(credential: str) -> GoogleIdentity:
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleAuthNotConfiguredError()

    try:
        async with _verification_semaphore:
            claims = await asyncio.to_thread(
                id_token.verify_oauth2_token,
                credential,
                _google_request,
                settings.GOOGLE_CLIENT_ID,
            )
    except (GoogleAuthError, ValueError) as exc:
        raise InvalidGoogleCredentialError() from exc

    email = claims.get("email")
    subject = claims.get("sub")
    if (
        claims.get("email_verified") is not True
        or not isinstance(email, str)
        or not email
        or not isinstance(subject, str)
        or not subject
    ):
        raise InvalidGoogleCredentialError()

    return GoogleIdentity(email=email.lower(), subject=subject)
