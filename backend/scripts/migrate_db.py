from services.migration_service import run_migrations


def main():
    result = run_migrations()
    executed = result["executed"]
    if executed:
        for item in executed:
            print(f"applied {item['version']} {item['name']}")
    else:
        print("database schema is already up to date")


if __name__ == "__main__":
    main()
