import pytest
from unittest.mock import patch, MagicMock
import mongomock
from pymongo import MongoClient
from src.normalizer.database import MongoDBHandler

@pytest.fixture
def mock_mongo_client():
  
    return mongomock.MongoClient()

@pytest.fixture
def db_handler(mock_mongo_client):
    
    handler = MongoDBHandler()
    handler.client = mock_mongo_client
    handler.db = mock_mongo_client['eduscrap_test']
    return handler

def test_upsert_new_document(db_handler):
   
    doc = {
        'titulo': 'Test Opportunity',
        'descricao': 'Test Description',
        'fonte': 'test_source',
        'link': 'https://example.com/test',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    # Perform upsert
    result = db_handler.upsert_documento(doc, 'test_collection', 'link')
    
    # Verify the document was inserted
    assert result is not None
    collection = db_handler.db['test_collection']
    stored_doc = collection.find_one({'link': 'https://example.com/test'})
    assert stored_doc is not None
    assert stored_doc['titulo'] == 'Test Opportunity'

def test_upsert_duplicate_document(db_handler):
   
    doc1 = {
        'titulo': 'Original Title',
        'descricao': 'Original Description',
        'fonte': 'test_source',
        'link': 'https://example.com/test',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    result1 = db_handler.upsert_documento(doc1, 'test_collection', 'link')
    
   
    doc2 = {
        'titulo': 'Updated Title',
        'descricao': 'Updated Description',
        'fonte': 'test_source',
        'link': 'https://example.com/test',
        'timestamp': '2023-01-02T00:00:00Z'
    }
    
    result2 = db_handler.upsert_documento(doc2, 'test_collection', 'link')
    
    collection = db_handler.db['test_collection']
    count = collection.count_documents({'link': 'https://example.com/test'})
    
   
    assert count == 1
    
    stored_doc = collection.find_one({'link': 'https://example.com/test'})
    assert stored_doc['titulo'] == 'Updated Title'
    assert stored_doc['descricao'] == 'Updated Description'

def test_deduplication_same_content_different_links(db_handler):
   
    doc1 = {
        'titulo': 'Same Title',
        'descricao': 'Same Description',
        'fonte': 'test_source',
        'link': 'https://example.com/test1',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    doc2 = {
        'titulo': 'Same Title',
        'descricao': 'Same Description',
        'fonte': 'test_source',
        'link': 'https://example.com/test2',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    db_handler.upsert_documento(doc1, 'test_collection', 'link')
    db_handler.upsert_documento(doc2, 'test_collection', 'link')
    
    collection = db_handler.db['test_collection']
    count = collection.count_documents({'titulo': 'Same Title'})
    assert count == 2

def test_deduplication_different_content_same_link(db_handler):
    
    doc1 = {
        'titulo': 'Original Title',
        'descricao': 'Original Description',
        'fonte': 'test_source',
        'link': 'https://example.com/same-link',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    db_handler.upsert_documento(doc1, 'test_collection', 'link')
    
    doc2 = {
        'titulo': 'New Title',
        'descricao': 'New Description',
        'fonte': 'test_source',
        'link': 'https://example.com/same-link',
        'timestamp': '2023-01-02T00:00:00Z'
    }
    
    db_handler.upsert_documento(doc2, 'test_collection', 'link')
    
    collection = db_handler.db['test_collection']
    count = collection.count_documents({'link': 'https://example.com/same-link'})
    assert count == 1
    
    stored_doc = collection.find_one({'link': 'https://example.com/same-link'})
    assert stored_doc['titulo'] == 'New Title'
    assert stored_doc['descricao'] == 'New Description'

def test_upsert_multiple_collections(db_handler):
   
    doc1 = {
        'titulo': 'Editais Doc',
        'fonte': 'ciee',
        'link': 'https://ciee.example.com/test',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    doc2 = {
        'titulo': 'Vagas Doc',
        'fonte': 'uern',
        'link': 'https://uern.example.com/test',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    db_handler.upsert_documento(doc1, 'editais', 'link')
    db_handler.upsert_documento(doc2, 'vagas', 'link')
    
    editais_count = db_handler.db['editais'].count_documents({})
    vagas_count = db_handler.db['vagas'].count_documents({})
    
    assert editais_count == 1
    assert vagas_count == 1

def test_upsert_with_custom_identifier_field(db_handler):
   
    doc1 = {
        'titulo': 'Custom ID Test',
        'descricao': 'Document with custom ID field',
        'fonte': 'test_source',
        'custom_id': 'ABC123',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    # Use 'custom_id' as identifier instead of 'link'
    result1 = db_handler.upsert_documento(doc1, 'test_collection', 'custom_id')
    
    # Try to upsert with same custom_id but different content
    doc2 = {
        'titulo': 'Updated Custom ID Test',
        'descricao': 'Updated document with same custom ID',
        'fonte': 'test_source',
        'custom_id': 'ABC123',
        'timestamp': '2023-01-02T00:00:00Z'
    }
    
    result2 = db_handler.upsert_documento(doc2, 'test_collection', 'custom_id')
    
    # Should have only 1 document with updated content
    collection = db_handler.db['test_collection']
    count = collection.count_documents({'custom_id': 'ABC123'})
    assert count == 1
    
    stored_doc = collection.find_one({'custom_id': 'ABC123'})
    assert stored_doc['titulo'] == 'Updated Custom ID Test'

def test_upsert_preserves_object_id(db_handler):
    """Test that upsert preserves the _id field correctly during updates"""
    doc1 = {
        'titulo': 'ID Preservation Test',
        'fonte': 'test_source',
        'link': 'https://example.com/id-test',
        'timestamp': '2023-01-01T00:00:00Z'
    }
    
    # Insert document
    result1 = db_handler.upsert_documento(doc1, 'test_collection', 'link')
    
    # Get the original document to capture its _id
    collection = db_handler.db['test_collection']
    original_doc = collection.find_one({'link': 'https://example.com/id-test'})
    original_id = original_doc['_id']
    
    # Update the document
    doc2 = {
        'titulo': 'Updated ID Preservation Test',
        'fonte': 'test_source',
        'link': 'https://example.com/id-test',
        'timestamp': '2023-01-02T00:00:00Z'
    }
    
    result2 = db_handler.upsert_documento(doc2, 'test_collection', 'link')
    
    # Get the updated document
    updated_doc = collection.find_one({'link': 'https://example.com/id-test'})
    updated_id = updated_doc['_id']
    
    # The _id should remain the same (document was updated, not replaced)
    assert original_id == updated_id
    assert updated_doc['titulo'] == 'Updated ID Preservation Test'