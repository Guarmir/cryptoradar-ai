"""Internal Google Play acknowledgement transport. No public route or activation."""
from urllib.parse import quote


class SubscriptionAcknowledgementError(Exception):
    """Safe error, without purchase credentials."""


class GooglePlaySubscriptionAcknowledger:
    def __init__(self, *, package_name, product_id, credentials_provider=None,
                 http_post=None):
        self._package = package_name.strip()
        self._product = product_id.strip()
        if not self._package or not self._product:
            raise ValueError('Package and product required.')
        self._credentials_provider = credentials_provider
        self._http_post = http_post

    def acknowledge(self, purchase_token):
        if not isinstance(purchase_token, str) or not purchase_token.strip():
            raise ValueError('Purchase token required.')
        try:
            if self._credentials_provider is None:
                import google.auth
                credentials, _ = google.auth.default(scopes=[
                    'https://www.googleapis.com/auth/androidpublisher'])
            else:
                credentials = self._credentials_provider()
            if not credentials.valid:
                from google.auth.transport.requests import Request
                credentials.refresh(Request())
            if not credentials.valid or not credentials.token:
                raise SubscriptionAcknowledgementError('Google credentials unavailable.')
            if self._http_post is None:
                import requests
                post = requests.post
            else:
                post = self._http_post
            url = ('https://androidpublisher.googleapis.com/androidpublisher/v3/'
                   f'applications/{quote(self._package, safe="")}/purchases/subscriptions/'
                   f'{quote(self._product, safe="")}/tokens/'
                   f'{quote(purchase_token.strip(), safe="")}:acknowledge')
            response = post(url, headers={'Authorization': f'Bearer {credentials.token}'},
                            json={}, timeout=15, allow_redirects=False)
            if response.status_code not in (200, 204):
                raise SubscriptionAcknowledgementError('Google acknowledgement unavailable.')
        except Exception:
            raise SubscriptionAcknowledgementError('Google acknowledgement unavailable.') from None
