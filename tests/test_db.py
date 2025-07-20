from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)


def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM products LIMIT 5;"))
            print("✅ Connexion réussie à la base Supabase")
            for row in result:
                print(row)
    except SQLAlchemyError as e:
        print("❌ Erreur de connexion :", e)


if __name__ == "__main__":
    test_connection()
