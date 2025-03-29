from models import Base, engine


def main():
    # Create all tables
    try:
        Base.metadata.create_all(engine)
        print("Database initialized and tables created.")
    except Exception as e:
        print(f"Error initializing the database: {e}")


if __name__ == "__main__":
    main()
