from app.main import app


def test_alert_route_is_registered_once() -> None:
    matches = [
        route
        for route in app.routes
        if (
            route.path
            == "/alert/{coin}/{price}"
        )
    ]

    assert len(matches) == 1
    assert "GET" in matches[0].methods