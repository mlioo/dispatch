"""
.. module: dispatch.plugins.dispatch_core.plugin
    :platform: Unix
    :copyright: (c) 2019 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
"""
import logging

import requests
from fastapi import HTTPException
from typing import List
from fastapi.security.utils import get_authorization_scheme_param

from jose import JWTError, jwt
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.requests import Request

from dispatch.config import DISPATCH_UI_URL
from dispatch.individual import service as individual_service
from dispatch.plugins import dispatch_core as dispatch_plugin
from dispatch.plugins.base import plugins
from dispatch.plugins.bases import (
    ParticipantPlugin,
    DocumentResolverPlugin,
    AuthenticationProviderPlugin,
    TicketPlugin,
)

from dispatch.route import service as route_service
from dispatch.route.models import RouteRequest

from dispatch.config import DISPATCH_AUTHENTICATION_PROVIDER_PKCE_JWKS, DISPATCH_JWT_SECRET

log = logging.getLogger(__name__)


class BasicAuthProviderPlugin(AuthenticationProviderPlugin):
    title = "Dispatch Plugin - Basic Authentication Provider"
    slug = "dispatch-auth-provider-basic"
    description = "Generic basic authentication provider."
    version = dispatch_plugin.__version__

    author = "Netflix"
    author_url = "https://github.com/netflix/dispatch.git"

    def get_current_user(self, request: Request, **kwargs):
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            return

        token = authorization.split()[1]

        try:
            data = jwt.decode(token, DISPATCH_JWT_SECRET)
        except JWTError as e:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))
        return data["email"]


class PKCEAuthProviderPlugin(AuthenticationProviderPlugin):
    title = "Dispatch Plugin - PKCE Authentication Provider"
    slug = "dispatch-auth-provider-pkce"
    description = "Generic PCKE authentication provider."
    version = dispatch_plugin.__version__

    author = "Netflix"
    author_url = "https://github.com/netflix/dispatch.git"

    def get_iap_key(key_id):
        """Retrieves a public key from the list published by Identity-Aware Proxy,
        re-fetching the key file if necessary.
        """
        key_cache = get_iap_key.key_cache
        key = key_cache.get(key_id)
        if not key:
            # Re-fetch the key file.
            resp = requests.get(
                'https://www.gstatic.com/iap/verify/public_key')
            if resp.status_code != 200:
                raise Exception(
                    'Unable to fetch IAP keys: {} / {} / {}'.format(
                        resp.status_code, resp.headers, resp.text))
            key_cache = resp.json()
            get_iap_key.key_cache = key_cache
            key = key_cache.get(key_id)
            if not key:
                raise Exception('Key {!r} not found'.format(key_id))
        return key

    def get_current_user(self, request: Request, **kwargs):
        credentials_exception = HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
        )

        authorization: str = request.headers.get("x-goog-iap-jwt-assertion")
        scheme, param = get_authorization_scheme_param(authorization)
        # if not authorization or scheme.lower() != "bearer":
        #     raise credentials_exception

        token = authorization


        key = get_iap_key

        try:
            data = jwt.decode(token, key)
        except JWTError:
            raise credentials_exception

        return data["email"]

    get_iap_key.key_cache = {}

class IAPAuthProviderPlugin(AuthenticationProviderPlugin):
    title = "Dispatch Plugin - GCP IAM Authentication Provider"
    slug = "dispatch-auth-provider-iap"
    description = "IAP authentication provider."
    version = dispatch_plugin.__version__

    author = "mlioo"
    author_url = "https://github.com/mlioo"

    get_iap_key.key_cache = {}

    def get_iap_key(key_id):
        """Retrieves a public key from the list published by Identity-Aware Proxy,
        re-fetching the key file if necessary.
        """
        key_cache = get_iap_key.key_cache
        key = key_cache.get(key_id)
        if not key:
            # Re-fetch the key file.
            resp = requests.get(
                'https://www.gstatic.com/iap/verify/public_key')
            if resp.status_code != 200:
                raise Exception(
                    'Unable to fetch IAP keys: {} / {} / {}'.format(
                        resp.status_code, resp.headers, resp.text))
            key_cache = resp.json()
            get_iap_key.key_cache = key_cache
            key = key_cache.get(key_id)
            if not key:
                raise Exception('Key {!r} not found'.format(key_id))
        return key

    def get_current_user(self, request: Request, **kwargs):
        credentials_exception = HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
        )

        authorization: str = request.headers.get("x-goog-iap-jwt-assertion")
        scheme, param = get_authorization_scheme_param(authorization)

        token = authorization
        key = get_iap_key

        try:
            data = jwt.decode(token, key)
        except JWTError:
            raise credentials_exception

        return data["email"]


class DispatchTicketPlugin(TicketPlugin):
    title = "Dispatch Plugin - Ticket Management"
    slug = "dispatch-ticket"
    description = "Uses dispatch itself to create a ticket."
    version = dispatch_plugin.__version__

    author = "Netflix"
    author_url = "https://github.com/netflix/dispatch.git"

    def create(
        self,
        incident_id: int,
        title: str,
        incident_type: str,
        incident_priority: str,
        commander: str,
        reporter: str,
    ):
        """Creates a dispatch ticket."""
        resource_id = f"dispatch-{incident_id}"
        return {
            "resource_id": resource_id,
            "weblink": f"{DISPATCH_UI_URL}/incidents/{resource_id}",
            "resource_type": "dispatch-internal-ticket",
        }

    def update(
        self,
        ticket_id: str,
        title: str = None,
        description: str = None,
        incident_type: str = None,
        priority: str = None,
        status: str = None,
        commander_email: str = None,
        reporter_email: str = None,
        conversation_weblink: str = None,
        conference_weblink: str = None,
        document_weblink: str = None,
        storage_weblink: str = None,
        labels: List[str] = None,
        cost: str = None,
    ):
        """Updates the incident."""
        return


class DispatchDocumentResolverPlugin(DocumentResolverPlugin):
    title = "Dispatch Plugin - Document Resolver"
    slug = "dispatch-document-resolver"
    description = "Uses dispatch itself to resolve incident documents."
    version = dispatch_plugin.__version__

    author = "Netflix"
    author_url = "https://github.com/netflix/dispatch.git"

    def get(
        self, incident_type: str, incident_priority: str, incident_description: str, db_session=None
    ):
        """Fetches documents from Dispatch."""
        route_in = {
            "text": incident_description,
            "context": {
                "incident_priorities": [incident_priority],
                "incident_types": [incident_type],
                "terms": [],
            },
        }

        route_in = RouteRequest(**route_in)
        recommendation = route_service.get(db_session=db_session, route_in=route_in)
        return recommendation.documents


class DispatchParticipantResolverPlugin(ParticipantPlugin):
    title = "Dispatch Plugin - Participant Resolver"
    slug = "dispatch-participant-resolver"
    description = "Uses dispatch itself to resolve incident participants."
    version = dispatch_plugin.__version__

    author = "Netflix"
    author_url = "https://github.com/netflix/dispatch.git"

    def get(
        self, incident_type: str, incident_priority: str, incident_description: str, db_session=None
    ):
        """Fetches participants from Dispatch."""
        route_in = {
            "text": incident_description,
            "context": {
                "incident_priorities": [incident_priority.__dict__],
                "incident_types": [incident_type.__dict__],
                "terms": [],
            },
        }

        route_in = RouteRequest(**route_in)
        recommendation = route_service.get(db_session=db_session, route_in=route_in)

        log.debug(f"Recommendation: {recommendation}")
        # we need to resolve our service contacts to individuals
        for s in recommendation.service_contacts:
            p = plugins.get(s.type)
            log.debug(f"Resolving service contact. ServiceContact: {s}")
            individual_email = p.get(s.external_id)

            individual = individual_service.get_or_create(
                db_session=db_session, email=individual_email
            )
            recommendation.individual_contacts.append(individual)

        db_session.commit()
        return list(recommendation.individual_contacts), list(recommendation.team_contacts)
