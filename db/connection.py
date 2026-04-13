import os
import psycopg2
# from sqlalchemy import create_engine
# from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    try:
        return psycopg2.connect( 
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"))
    except psycopg2.OperationalError as e:
         print(f"Erreur de connexion : {e}")
         raise

# def get_engine():
#     try:
#         url = (
#             f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
#             f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
#         )
#         engine = create_engine(url, pool_size=5, max_overflow=10)
#         return engine
#     except SQLAlchemyError as e:
#         print(f"Erreur de connexion : {e}")
#         raisecd do    