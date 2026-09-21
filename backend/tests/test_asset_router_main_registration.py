from app.main import app


def test_asset_routes_are_registered_once() -> None:
    expected_routes = {
        "/analysis/{symbol}",
        "/price/{coin}",
        "/score/{coin}",
        "/chart/{coin}",
        "/asset/{coin}",
    }

    for expected_path in expected_routes:
        matches = [
            route
            for route in app.routes
            if route.path == expected_path
        ]

        assert len(matches) == 1

        assert "GET" in matches[0].methods