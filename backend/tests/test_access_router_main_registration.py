from app.main import app


def test_access_route_is_registered_once() -> None:
    matches = [
        route
        for route in app.routes
        if (
            route.path
            == "/access/entitlements/{installation_id}"
        )
    ]

    assert len(matches) == 1
    assert "GET" in matches[0].methods