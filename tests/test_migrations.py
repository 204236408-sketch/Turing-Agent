def test_migrations_are_idempotent_on_empty_sqlite():
    from database import init_database

    init_database()
    init_database()
