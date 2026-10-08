import sys
from pathlib import Path
import os

# Add backend and backend/src to the Python path
backend_path = Path(__file__).parent / 'backend'
src_path = Path(__file__).parent / 'backend' / 'src'

# Insert both paths at the beginning of sys.path
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(src_path))

# Also add the normalizer directory from backend
normalizer_path = src_path / 'normalizer'
sys.path.insert(0, str(normalizer_path))

# Patch MongoClient before importing the app to avoid connecting to actual MongoDB
import mongomock
from unittest.mock import patch

# Mock MongoDB connection globally
mongo_patcher = patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

def pytest_configure(config):
    """Configuration hook for pytest"""
    pass

def pytest_unconfigure(config):
    """Cleanup hook for pytest"""
    mongo_patcher.stop()