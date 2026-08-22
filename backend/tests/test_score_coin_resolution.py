import unittest
from unittest.mock import patch

from app.services.score import resolve_coin


class ScoreCoinResolutionTest(
    unittest.TestCase
):
    def test_btc_resolves_to_bitcoin_without_search(
        self,
    ):
        with patch(
            "app.services.score.requests.get"
        ) as requests_get:
            result = resolve_coin(
                "BTC"
            )

        self.assertEqual(
            result["id"],
            "bitcoin",
        )

        requests_get.assert_not_called()

    def test_eth_resolves_to_ethereum_without_search(
        self,
    ):
        with patch(
            "app.services.score.requests.get"
        ) as requests_get:
            result = resolve_coin(
                "eth"
            )

        self.assertEqual(
            result["id"],
            "ethereum",
        )

        requests_get.assert_not_called()

    def test_sol_resolves_to_solana_without_search(
        self,
    ):
        with patch(
            "app.services.score.requests.get"
        ) as requests_get:
            result = resolve_coin(
                " SOL "
            )

        self.assertEqual(
            result["id"],
            "solana",
        )

        requests_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()