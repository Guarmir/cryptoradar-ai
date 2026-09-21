from app.main import app


def test_radar_ai_router_is_registered() -> None:
    radar_route = next(
        (
            route
            for route in app.routes
            if route.path == "/ai/radar/ask"
        ),
        None,
    )

    assert radar_route is not None
    assert "POST" in radar_route.methods