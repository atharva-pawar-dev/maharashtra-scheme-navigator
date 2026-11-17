    @classmethod
    def for_runtime(
        cls,
        *,
        configured_path: str | Path | None,
        demo_fixtures_enabled: bool,
    ) -> "SchemeCatalog":
        """Load a configured catalog, demo fixtures, or an empty catalog."""
        if configured_path:
            return cls.from_json(configured_path)

        if demo_fixtures_enabled:
            return cls.from_json()

        return cls([])