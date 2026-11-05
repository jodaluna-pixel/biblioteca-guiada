import os
from dotenv import load_dotenv
load_dotenv()
 
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///biblioteca.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENLIBRARY_CONTACT = os.getenv("OPENLIBRARY_CONTACT", "jodaluna@gmail.com")

