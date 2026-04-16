from sqlalchemy import text

from database import engine


def run_postgres_migration():
    statements = [
        "ALTER TABLE dispensaries ADD COLUMN IF NOT EXISTS place_id VARCHAR",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_dispensaries_place_id_not_null ON dispensaries(place_id) WHERE place_id IS NOT NULL",
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def main():
    run_postgres_migration()
    print("Migration complete: dispensaries.place_id + unique partial index")


if __name__ == "__main__":
    main()
