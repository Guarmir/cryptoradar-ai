import unittest
from unittest.mock import patch

from app.main import resolve_coin_id


class CoinIdResolutionTest(
    unittest.TestCase
):
    def test_btc_resolves_to_bitcoin(
        self,
    ):
        with patch(
            "app.main.get_coin_list"
        ) as get_coin_list:
            result = resolve_coin_id(
                "BTC"
            )

        self.assertEqual(
            result,
            "bitcoin",
        )

        get_coin_list.assert_not_called()

    def test_eth_resolves_to_ethereum(
        self,
    ):
        with patch(
            "app.main.get_coin_list"
        ) as get_coin_list:
            result = resolve_coin_id(
                "eth"
            )

        self.assertEqual(
            result,
            "ethereum",
        )

        get_coin_list.assert_not_called()

    def test_sol_resolves_to_solana(
        self,
    ):
        with patch(
            "app.main.get_coin_list"
        ) as get_coin_list:
            result = resolve_coin_id(
                " SOL "
            )

        self.assertEqual(
            result,
            "solana",
        )

        get_coin_list.assert_not_called()

    def test_existing_exact_id_resolution_is_preserved(
        self,
    ):
        coins = [
            {
                "id": "example-coin",
                "symbol": "exm",
                "name": "Example Coin",
            }
        ]

        with patch(
            "app.main.get_coin_list",
            return_value=coins,
        ):
            result = resolve_coin_id(
                "example-coin"
            )

        self.assertEqual(
            result,
            "example-coin",
        )

    def test_existing_exact_name_resolution_is_preserved(
        self,
    ):
        coins = [
            {
                "id": "example-coin",
                "symbol": "exm",
                "name": "Example Coin",
            }
        ]

        with patch(
            "app.main.get_coin_list",
            return_value=coins,
        ):
            result = resolve_coin_id(
                "Example Coin"
            )

        self.assertEqual(
            result,
            "example-coin",
        )


if __name__ == "__main__":
    unittest.main()