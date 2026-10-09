import sys
from pathlib import Path
import os

backend_path = Path(__file__).parent / 'backend'
src_path = Path(__file__).parent / 'backend' / 'src'

sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(src_path))

normalizer_path = src_path / 'normalizer'
sys.path.insert(0, str(normalizer_path))

import mongomock
from unittest.mock import patch

mongo_patcher = patch('pymongo.MongoClient', mongomock.MongoClient)
mongo_patcher.start()

def pytest_configure(config):
   
    pass

def pytest_unconfigure(config):
   
    mongo_patcher.stop()