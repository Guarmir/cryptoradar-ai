
import os
from pathlib import Path

import psycopg


DATABASE_ENV_NAME = "CRYPTORADAR_DATABASE_URL"

MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent
    / "migrations"
    / "006_early_movement_direction_history.sql"
)


def main() -> None:
    database_url = os.environ.get(
        DATABASE_ENV_NAME,
        "",
    ).strip()

    if not database_url:
        raise SystemExit(
            "CRYPTORADAR_DATABASE_URL "
            "nao esta configurada."
        )

    if not MIGRATION_FILE.exists():
        raise SystemExit(
            "Migracao 006 nao encontrada."
        )

    migration_sql = MIGRATION_FILE.read_text(
        encoding="utf-8",
    )

    connection = psycopg.connect(
        database_url,
    )

    try:
        cursor = connection.cursor()

        try:
            cursor.execute(migration_sql)
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()

    finally:
        connection.close()

    print(
        "MIGRATION 006 EARLY MOVEMENT "
        "DIRECTION OK"
    )


if __name__ == "__main__":
    main()
