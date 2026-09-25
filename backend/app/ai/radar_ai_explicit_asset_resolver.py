class RadarAIExplicitAssetResolver:
    def __init__(
        self,
        asset_id: str,
    ) -> None:
        normalized_asset_id = (
            asset_id.strip()
        )

        if not normalized_asset_id:
            raise ValueError(
                "asset_id must not be empty"
            )

        self._asset_id = (
            normalized_asset_id
        )

    def resolve(
        self,
        question: str,
    ) -> str:
        return self._asset_id