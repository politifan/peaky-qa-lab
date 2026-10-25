"""Baseline service entrypoint for uvicorn and local Locust work."""
import os
from seatlab.app import create_app
app=create_app(os.environ.get('SEATLAB_DB','data/subject.db'),os.environ.get('SEATLAB_PROFILE','good'))
