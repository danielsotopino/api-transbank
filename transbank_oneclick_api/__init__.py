from fastapi import FastAPI

from transbank_oneclick_api.database import init_db


def setup_subscription_manager(app: FastAPI, database_url: str):
    """Complete setup for subscription manager"""
    # Initialize database
    init_db(database_url)