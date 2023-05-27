from pathlib import Path

from decouple import config


BASE_DIR = Path(__file__).resolve().parent

config.search_path = BASE_DIR


class Config:
    LINKEDIN_USERNAME = config("LINKEDIN_USERNAME", cast=str)
    LINKEDIN_PASSWORD = config("LINKEDIN_PASSWORD", cast=str)
    LINKEDIN_JOB_SEARCH = config("LINKEDIN_JOB_SEARCH", cast=str)
    LINKEDIN_JOB_LOCATION = config("LINKEDIN_JOB_LOCATION", cast=str)



config = Config()