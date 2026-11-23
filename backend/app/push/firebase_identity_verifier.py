"""Verificacao de identidade Firebase para endpoints protegidos.

Nao autoriza o acesso a uma instalacao por si so: essa verificacao deve
ser combinada com um vinculo persistente entre UID e installation_id.
"""

from collections.abc import Callable, Mapping
from typing import Any

from fastapi import HTTPException, status


class FirebaseIdentityVerifier:
    def __init__(
        self,
        *,
        token_verifier: Callable[[str], Mapping[str, Any]] | None = None,
    ) -> None:
        self._token_verifier = token_verifier

    def verify_bearer(self, authorization: str | None) -> str:
        """Retorna UID autenticado ou HTTP 401; nunca confia no UID do cliente."""
        if not isinstance(authorization, str):
            raise self._unauthorized()

        parts = authorization.strip().split()
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
            raise self._unauthorized()

        try:
            claims = self._verify_token(parts[1])
            if not isinstance(claims, Mapping):
                raise ValueError("invalid claims")
            uid = claims.get("uid") or claims.get("sub")
            if not isinstance(uid, str) or not uid.strip():
                raise ValueError("missing uid")
            return uid.strip()
        except Exception as exc:
            raise self._unauthorized() from exc

    def _verify_token(self, token: str) -> Mapping[str, Any]:
        if self._token_verifier is not None:
            return self._token_verifier(token)

        import firebase_admin
        from firebase_admin import auth

        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()

        return auth.verify_id_token(token, check_revoked=True)

    @staticmethod
    def _unauthorized() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticacao Firebase invalida ou ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
