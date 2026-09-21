from app.main import app


def test_push_route_is_registered_once() -> None:
    matches = [
        route
        for route in app.routes
        if (
            route.path
            == "/push/devices/register"
        )
    ]

    assert len(matches) == 1
    assert "POST" in matches[0].methods