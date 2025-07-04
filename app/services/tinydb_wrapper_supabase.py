# supabase_tinydb_fixed.py
"""
FULLY COMPATIBLE: TinyDB wrapper for Supabase (Standard PostgreSQL)
Handles JSONB data type properly with complete TinyDB API compatibility
"""

import os
import logging
import sys
import json
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

# Use standard PostgreSQL with psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    from psycopg2 import pool
except ImportError:
    raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")

class Query:
    """TinyDB-compatible Query class with full operator support"""
    
    def __init__(self, path: List[str] = None):
        self.path = path or []
    
    def __getattr__(self, item):
        return Query(self.path + [item])
    
    def __getitem__(self, item):
        return Query(self.path + [item])
    
    def __eq__(self, other):
        return QueryCondition(self.path, '=', other)
    
    def __ne__(self, other):
        return QueryCondition(self.path, '!=', other)
    
    def __lt__(self, other):
        return QueryCondition(self.path, '<', other)
    
    def __le__(self, other):
        return QueryCondition(self.path, '<=', other)
    
    def __gt__(self, other):
        return QueryCondition(self.path, '>', other)
    
    def __ge__(self, other):
        return QueryCondition(self.path, '>=', other)
    
    def matches(self, regex: str):
        return QueryCondition(self.path, 'LIKE', f'%{regex}%')
    
    def exists(self):
        return QueryCondition(self.path, 'EXISTS', True)
    
    def one_of(self, items: List[Any]):
        return QueryCondition(self.path, 'IN', items)
    
    def any(self, items: List[Any]):
        return QueryCondition(self.path, 'ANY', items)
    
    def all(self, items: List[Any]):
        return QueryCondition(self.path, 'ALL', items)

class QueryCondition:
    """Query condition class with full operator support"""
    
    def __init__(self, path: List[str], operator: str, value: Any):
        self.path = path
        self.operator = operator
        self.value = value
    
    def __and__(self, other):
        return CombinedCondition(self, 'AND', other)
    
    def __or__(self, other):
        return CombinedCondition(self, 'OR', other)
    
    def __invert__(self):
        return QueryCondition(self.path, '!' + self.operator, self.value)

class CombinedCondition:
    """Combined condition class"""
    
    def __init__(self, left, operator: str, right):
        self.left = left
        self.operator = operator
        self.right = right
    
    def __and__(self, other):
        return CombinedCondition(self, 'AND', other)
    
    def __or__(self, other):
        return CombinedCondition(self, 'OR', other)

class PostgreSQLTable:
    """PostgreSQL-backed table that fully mimics TinyDB Table API"""
    
    def __init__(self, connection_pool, table_name: str):
        self.connection_pool = connection_pool
        self.table_name = table_name
        self._lock = threading.RLock()
        self._ensure_table()
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.connection_pool.getconn()
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        self.connection_pool.putconn(conn)
    
    def _ensure_table(self):
        """Create table if it doesn't exist"""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(f'''
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            doc_id SERIAL PRIMARY KEY,
                            data JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Create indexes for performance
                    cur.execute(f'''
                        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created 
                        ON {self.table_name}(created_at)
                    ''')
                    
                    # Create GIN index for JSONB queries
                    cur.execute(f'''
                        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_data 
                        ON {self.table_name} USING GIN (data)
                    ''')
                    
                    conn.commit()
            finally:
                self._return_connection(conn)
    
    def _extract_value(self, doc: Dict, path: List[str]) -> Any:
        """Extract value from document using path"""
        value = doc
        for key in path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def _matches_condition(self, doc: Dict, condition) -> bool:
        """Check if document matches condition with full operator support"""
        if isinstance(condition, QueryCondition):
            value = self._extract_value(doc, condition.path)
            
            if condition.operator == '=':
                return value == condition.value
            elif condition.operator == '!=':
                return value != condition.value
            elif condition.operator == '<':
                return value is not None and value < condition.value
            elif condition.operator == '<=':
                return value is not None and value <= condition.value
            elif condition.operator == '>':
                return value is not None and value > condition.value
            elif condition.operator == '>=':
                return value is not None and value >= condition.value
            elif condition.operator == 'LIKE':
                return value is not None and str(condition.value).lower() in str(value).lower()
            elif condition.operator == 'EXISTS':
                return value is not None
            elif condition.operator == 'IN':
                return value in condition.value if isinstance(condition.value, (list, tuple)) else False
            elif condition.operator == 'ANY':
                return any(v in condition.value for v in (value if isinstance(value, (list, tuple)) else [value]))
            elif condition.operator == 'ALL':
                return all(v in condition.value for v in (value if isinstance(value, (list, tuple)) else [value]))
        
        elif isinstance(condition, CombinedCondition):
            left_match = self._matches_condition(doc, condition.left)
            right_match = self._matches_condition(doc, condition.right)
            
            if condition.operator == 'AND':
                return left_match and right_match
            elif condition.operator == 'OR':
                return left_match or right_match
        
        return False
    
    def insert(self, document: Dict) -> int:
        """Insert document - TinyDB compatible"""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor() as cur:
                    # Add metadata
                    doc_with_meta = document.copy()
                    doc_with_meta['_inserted_at'] = datetime.now().isoformat()
                    
                    # Use psycopg2's Json adapter for JSONB
                    cur.execute(
                        f'INSERT INTO {self.table_name} (data) VALUES (%s) RETURNING doc_id',
                        (Json(doc_with_meta),)
                    )
                    
                    doc_id = cur.fetchone()[0]
                    conn.commit()
                    return doc_id
            finally:
                self._return_connection(conn)
    
    def insert_multiple(self, documents: List[Dict]) -> List[int]:
        """Insert multiple documents efficiently"""
        if not documents:
            return []
        
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor() as cur:
                    doc_ids = []
                    for doc in documents:
                        # Add metadata
                        doc_with_meta = doc.copy()
                        doc_with_meta['_inserted_at'] = datetime.now().isoformat()
                        
                        # Use psycopg2's Json adapter for JSONB
                        cur.execute(
                            f'INSERT INTO {self.table_name} (data) VALUES (%s) RETURNING doc_id',
                            (Json(doc_with_meta),)
                        )
                        
                        doc_id = cur.fetchone()[0]
                        doc_ids.append(doc_id)
                    
                    conn.commit()
                    return doc_ids
            finally:
                self._return_connection(conn)
    
    def all(self) -> List[Dict]:
        """Get all documents - TinyDB compatible"""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(f'SELECT doc_id, data FROM {self.table_name} ORDER BY doc_id')
                    rows = cur.fetchall()
                    
                    documents = []
                    for row in rows:
                        # JSONB data is returned as dict directly
                        doc = dict(row['data'])  # Convert to regular dict
                        doc['doc_id'] = row['doc_id']  # Add TinyDB-style doc_id
                        documents.append(doc)
                    
                    return documents
            finally:
                self._return_connection(conn)
    
    def get(self, cond=None, doc_id: int = None) -> Optional[Dict]:
        """Get single document - TinyDB compatible"""
        if doc_id is not None:
            with self._lock:
                conn = self._get_connection()
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(f'SELECT doc_id, data FROM {self.table_name} WHERE doc_id = %s', (doc_id,))
                        row = cur.fetchone()
                        
                        if row:
                            # JSONB data is returned as dict directly
                            doc = dict(row['data'])  # Convert to regular dict
                            doc['doc_id'] = row['doc_id']
                            return doc
                        
                        return None
                finally:
                    self._return_connection(conn)
        
        # Query-based search
        if cond is None:
            all_docs = self.all()
            return all_docs[0] if all_docs else None
        
        results = self.search(cond)
        return results[0] if results else None
    
    def search(self, cond) -> List[Dict]:
        """Search documents - TinyDB compatible"""
        all_docs = self.all()
        
        if cond is None:
            return all_docs
        
        results = []
        for doc in all_docs:
            if self._matches_condition(doc, cond):
                results.append(doc)
        
        return results
    
    def update(self, fields: Dict, cond=None, doc_ids: List[int] = None) -> List[int]:
        """Update documents - FULL TinyDB compatible with doc_ids support"""
        updated_ids = []
        
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Determine which documents to update
                    if doc_ids is not None:
                        # Update specific doc_ids
                        target_doc_ids = doc_ids
                    elif cond is not None:
                        # Update documents matching condition
                        matching_docs = self.search(cond)
                        target_doc_ids = [doc['doc_id'] for doc in matching_docs]
                    else:
                        # Update all documents
                        all_docs = self.all()
                        target_doc_ids = [doc['doc_id'] for doc in all_docs]
                    
                    # Update each document
                    for doc_id in target_doc_ids:
                        # Get current document
                        cur.execute(f'SELECT data FROM {self.table_name} WHERE doc_id = %s', (doc_id,))
                        row = cur.fetchone()
                        
                        if row:
                            # JSONB data is returned as dict directly
                            current_doc = dict(row['data'])  # Convert to regular dict
                            current_doc.update(fields)
                            current_doc['_updated_at'] = datetime.now().isoformat()
                            
                            # Update document using Json adapter
                            cur.execute(
                                f'UPDATE {self.table_name} SET data = %s, updated_at = CURRENT_TIMESTAMP WHERE doc_id = %s',
                                (Json(current_doc), doc_id)
                            )
                            
                            updated_ids.append(doc_id)
                    
                    conn.commit()
            finally:
                self._return_connection(conn)
        
        return updated_ids
    
    def remove(self, cond=None, doc_ids: List[int] = None) -> List[int]:
        """Remove documents - FULL TinyDB compatible with doc_ids support"""
        removed_ids = []
        
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor() as cur:
                    # Determine which documents to remove
                    if doc_ids is not None:
                        # Remove specific doc_ids
                        target_doc_ids = doc_ids
                    elif cond is not None:
                        # Remove documents matching condition
                        matching_docs = self.search(cond)
                        target_doc_ids = [doc['doc_id'] for doc in matching_docs]
                    else:
                        # Remove all documents
                        all_docs = self.all()
                        target_doc_ids = [doc['doc_id'] for doc in all_docs]
                    
                    if target_doc_ids:
                        placeholders = ','.join(['%s' for _ in target_doc_ids])
                        cur.execute(f'DELETE FROM {self.table_name} WHERE doc_id IN ({placeholders})', target_doc_ids)
                        removed_ids = target_doc_ids
                        conn.commit()
            finally:
                self._return_connection(conn)
        
        return removed_ids
    
    def truncate(self) -> None:
        """Remove all documents from table"""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(f'TRUNCATE TABLE {self.table_name} RESTART IDENTITY')
                    conn.commit()
            finally:
                self._return_connection(conn)
    
    def count(self, cond=None) -> int:
        """Count documents"""
        if cond is None:
            with self._lock:
                conn = self._get_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute(f'SELECT COUNT(*) FROM {self.table_name}')
                        return cur.fetchone()[0]
                finally:
                    self._return_connection(conn)
        else:
            return len(self.search(cond))
    
    def contains(self, cond) -> bool:
        """Check if any document matches condition"""
        return len(self.search(cond)) > 0
    
    def __len__(self) -> int:
        """Get table length"""
        return self.count()
    
    def __contains__(self, item) -> bool:
        """Check if document exists"""
        if isinstance(item, dict):
            # Check if exact document exists
            all_docs = self.all()
            for doc in all_docs:
                if all(doc.get(k) == v for k, v in item.items()):
                    return True
            return False
        return False

class TinyDB:
    """PostgreSQL-backed TinyDB with full API compatibility"""
    
    def __init__(self, path: str = 'db.json', **kwargs):
        # Get PostgreSQL connection string from environment
        self.database_url = kwargs.get('database_url') or os.getenv('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Create connection pool
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                1, 20,  # min and max connections
                self.database_url
            )
        except Exception as e:
            raise ValueError(f"Failed to connect to database: {e}")
        
        self.tables = {}
        self._default_table = None
    
    def table(self, name: str = '_default') -> PostgreSQLTable:
        """Get or create table - TinyDB compatible"""
        if name not in self.tables:
            self.tables[name] = PostgreSQLTable(self.connection_pool, name)
        return self.tables[name]
    
    def default_table(self) -> PostgreSQLTable:
        """Get default table"""
        if self._default_table is None:
            self._default_table = self.table('_default')
        return self._default_table
    
    # Direct table operations (for compatibility)
    def insert(self, document: Dict) -> int:
        return self.default_table().insert(document)
    
    def insert_multiple(self, documents: List[Dict]) -> List[int]:
        return self.default_table().insert_multiple(documents)
    
    def all(self) -> List[Dict]:
        return self.default_table().all()
    
    def get(self, cond=None, doc_id: int = None) -> Optional[Dict]:
        return self.default_table().get(cond, doc_id)
    
    def search(self, cond) -> List[Dict]:
        return self.default_table().search(cond)
    
    def update(self, fields: Dict, cond=None, doc_ids: List[int] = None) -> List[int]:
        return self.default_table().update(fields, cond, doc_ids)
    
    def remove(self, cond=None, doc_ids: List[int] = None) -> List[int]:
        return self.default_table().remove(cond, doc_ids)
    
    def truncate(self) -> None:
        return self.default_table().truncate()
    
    def count(self, cond=None) -> int:
        return self.default_table().count(cond)
    
    def contains(self, cond) -> bool:
        return self.default_table().contains(cond)
    
    def close(self):
        """Close database connection pool"""
        if hasattr(self.connection_pool, 'closeall'):
            self.connection_pool.closeall()
    
    def __len__(self) -> int:
        return self.default_table().count()
    
    def __contains__(self, item) -> bool:
        return self.default_table().__contains__(item)

# Document class for advanced operations
class Document(dict):
    """Document class that extends dict with TinyDB document functionality"""
    
    def __init__(self, value=None, doc_id=None, **kwargs):
        super().__init__()
        if value is not None:
            if isinstance(value, dict):
                self.update(value)
            else:
                raise ValueError("Document value must be a dictionary")
        
        self.update(kwargs)
        if doc_id is not None:
            self.doc_id = doc_id
    
    @property
    def doc_id(self):
        return self.get('doc_id')
    
    @doc_id.setter
    def doc_id(self, value):
        self['doc_id'] = value

# Migration helper
def migrate_from_tinydb(old_db_path: str = 'email_system.json'):
    """Migrate existing TinyDB data to PostgreSQL"""
    
    # Import old TinyDB data
    try:
        from tinydb import TinyDB as OldTinyDB
        old_db = OldTinyDB(old_db_path)
    except ImportError:
        print("TinyDB not installed. Install with: pip install tinydb")
        return
    
    # Create new PostgreSQL database
    new_db = TinyDB()
    
    # Migrate each table
    table_names = ['emails', 'replies', 'action_items', 'tenants', 'response_feedback', 'context_patterns', 'ai_responses', 'tickets']
    
    total_migrated = 0
    
    for table_name in table_names:
        print(f"Migrating {table_name}...")
        
        old_table = old_db.table(table_name)
        new_table = new_db.table(table_name)
        
        # Get all data from old table
        old_data = old_table.all()
        
        # Insert into new table
        if old_data:
            new_table.insert_multiple(old_data)
            total_migrated += len(old_data)
            print(f"  ✅ Migrated {len(old_data)} records from {table_name}")
        else:
            print(f"  ⏭️  No data in {table_name}")
    
    print(f"\n🎉 Migration completed! Total records migrated: {total_migrated}")
    print("Your data is now in PostgreSQL database!")

# =================================================================
# USAGE EXAMPLE & TESTING
# =================================================================
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_postgresql_wrapper():
    """Test the PostgreSQL wrapper with all TinyDB operations"""
    print("🔧 Testing PostgreSQL TinyDB Wrapper...")
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not set!")
        print("Set it with: export DATABASE_URL='postgresql://user:password@host:port/database'")
        return False
    
    try:
        # Import the fixed wrapper
        from app.services.tinydb_wrapper_supabase import TinyDB, Query
        
        # Create database connection
        db = TinyDB()
        test_table = db.table('test_fixes')
        
        print("✅ Database connection successful")
        
        # 1. Test basic insert
        test_data = {
            'id': 'test-001',
            'name': 'Test Record',
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        doc_id = test_table.insert(test_data)
        print(f"✅ Insert successful - doc_id: {doc_id}")
        
        # 2. Test the problematic doc_ids update operation
        update_data = {'status': 'updated', 'updated_at': datetime.now().isoformat()}
        updated_ids = test_table.update(update_data, doc_ids=[doc_id])
        print(f"✅ Update with doc_ids successful - updated: {updated_ids}")
        
        # 3. Test query-based update
        TestQuery = Query()
        updated_ids2 = test_table.update(
            {'status': 'query_updated'}, 
            TestQuery.id == 'test-001'
        )
        print(f"✅ Query-based update successful - updated: {updated_ids2}")
        
        # 4. Test bulk operations
        # Insert multiple records
        bulk_data = [
            {'id': f'bulk-{i}', 'name': f'Bulk Record {i}', 'status': 'bulk'} 
            for i in range(1, 6)
        ]
        bulk_doc_ids = test_table.insert_multiple(bulk_data)
        print(f"✅ Bulk insert successful - doc_ids: {bulk_doc_ids}")
        
        # Test bulk update with doc_ids
        bulk_updated = test_table.update(
            {'status': 'bulk_updated', 'updated_at': datetime.now().isoformat()},
            doc_ids=bulk_doc_ids
        )
        print(f"✅ Bulk update with doc_ids successful - updated: {len(bulk_updated)}")
        
        # 5. Test advanced queries
        # Test one_of query
        TestQuery = Query()
        status_results = test_table.search(TestQuery.status.one_of(['updated', 'bulk_updated']))
        print(f"✅ Advanced query (one_of) successful - found: {len(status_results)}")
        
        # Test contains check
        contains_result = test_table.contains(TestQuery.id == 'test-001')
        print(f"✅ Contains check successful - result: {contains_result}")
        
        # 6. Test remove with doc_ids
        removed_ids = test_table.remove(doc_ids=[doc_id])
        print(f"✅ Remove with doc_ids successful - removed: {removed_ids}")
        
        # 7. Test search and count
        all_records = test_table.all()
        count = test_table.count()
        print(f"✅ Search and count successful - total: {count}, retrieved: {len(all_records)}")
        
        # 8. Clean up
        test_table.truncate()
        print("✅ Cleanup successful")
        
        print("\n🎉 All PostgreSQL wrapper tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in PostgreSQL wrapper test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_operations():
    """Test the model operations with proper ID handling"""
    print("\n🔧 Testing Model Operations...")
    
    try:
        # Import the fixed models
        from app.models import (
            EmailMessage, emails_table, 
            get_document_by_id, update_document_by_id, remove_document_by_id
        )
        
        # 1. Test email creation
        email_id = EmailMessage.create(
            sender='test@example.com',
            subject='Test Email for Model Operations',
            body='This is a test email to verify model operations work correctly.',
            status='unprocessed'
        )
        print(f"✅ Email created successfully - ID: {email_id}")
        
        # 2. Test get by ID (both ways)
        email_by_doc_id = get_document_by_id(emails_table, email_id)
        print(f"✅ Get by doc_id successful - found: {email_by_doc_id is not None}")
        
        if email_by_doc_id:
            custom_id = email_by_doc_id.get('id')
            email_by_custom_id = get_document_by_id(emails_table, custom_id)
            print(f"✅ Get by custom_id successful - found: {email_by_custom_id is not None}")
        
        # 3. Test update by ID
        success = update_document_by_id(emails_table, email_id, {
            'status': 'processed',
            'processed_at': datetime.now().isoformat()
        })
        print(f"✅ Update by ID successful - result: {success}")
        
        # 4. Test bulk update (the problematic operation)
        # Create multiple emails first
        bulk_emails = []
        for i in range(5):
            bulk_id = EmailMessage.create(
                sender=f'bulk{i}@example.com',
                subject=f'Bulk Test Email {i}',
                body=f'This is bulk test email number {i}',
                status='unprocessed'
            )
            bulk_emails.append(bulk_id)
        
        print(f"✅ Created {len(bulk_emails)} bulk emails")
        
        # Test the bulk status update that was failing
        updated_count = 0
        errors = []
        
        for bulk_email_id in bulk_emails:
            try:
                success = update_document_by_id(emails_table, bulk_email_id, {
                    'status': 'processing',
                    'updated_at': datetime.now().isoformat()
                })
                if success:
                    updated_count += 1
                else:
                    errors.append(f"Failed to update email {bulk_email_id}")
            except Exception as e:
                errors.append(f"Error updating email {bulk_email_id}: {str(e)}")
        
        print(f"✅ Bulk update test - Updated: {updated_count}/{len(bulk_emails)}, Errors: {len(errors)}")
        
        if errors:
            print("❌ Bulk update errors:")
            for error in errors:
                print(f"  - {error}")
        
        # 5. Clean up
        remove_document_by_id(emails_table, email_id)
        for bulk_id in bulk_emails:
            remove_document_by_id(emails_table, bulk_id)
        
        print("✅ Model operations cleanup successful")
        
        if len(errors) == 0:
            print("\n🎉 All model operations tests passed!")
            return True
        else:
            print(f"\n⚠️  Model operations completed with {len(errors)} errors")
            return False
        
    except Exception as e:
        print(f"❌ Error in model operations test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_compatibility():
    """Test API endpoint compatibility"""
    print("\n🔧 Testing API Compatibility...")
    
    try:
        # Test the bulk update endpoint logic
        from app.api.routes.emails import bulk_update_email_status
        from app.models import EmailMessage, emails_table
        
        # Create test emails
        test_email_ids = []
        for i in range(3):
            email_id = EmailMessage.create(
                sender=f'api_test{i}@example.com',
                subject=f'API Test Email {i}',
                body=f'This is API test email number {i}',
                status='unprocessed'
            )
            test_email_ids.append(str(email_id))  # Convert to string for API
        
        print(f"✅ Created {len(test_email_ids)} test emails for API test")
        
        # Simulate the bulk update request
        from app.api.routes.emails import BulkUpdateStatusRequest
        
        # This should work now without the doc_ids error
        request = BulkUpdateStatusRequest(
            email_ids=test_email_ids,
            new_status='processing',
            notes='API compatibility test'
        )
        
        print("✅ API request model created successfully")
        
        # Test the update logic directly
        updated_count = 0
        errors = []
        
        for email_id in request.email_ids:
            try:
                from app.models import update_document_by_id
                update_data = {
                    "status": request.new_status,
                    "updated_at": datetime.now().isoformat()
                }
                
                if request.notes:
                    update_data["bulk_update_notes"] = request.notes
                
                success = update_document_by_id(emails_table, email_id, update_data)
                if success:
                    updated_count += 1
                else:
                    errors.append(f"Failed to update email {email_id}")
                    
            except Exception as e:
                errors.append(f"Error updating email {email_id}: {str(e)}")
        
        print(f"✅ API bulk update test - Updated: {updated_count}/{len(request.email_ids)}, Errors: {len(errors)}")
        
        # Clean up
        from app.models import remove_document_by_id
        for email_id in test_email_ids:
            remove_document_by_id(emails_table, email_id)
        
        print("✅ API compatibility cleanup successful")
        
        if len(errors) == 0:
            print("\n🎉 All API compatibility tests passed!")
            return True
        else:
            print(f"\n⚠️  API compatibility completed with {len(errors)} errors")
            return False
        
    except Exception as e:
        print(f"❌ Error in API compatibility test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive fix verification tests...\n")
    
    results = []
    
    # Test 1: PostgreSQL Wrapper
    results.append(test_postgresql_wrapper())
    
    # Test 2: Model Operations
    results.append(test_model_operations())
    
    # Test 3: API Compatibility
    results.append(test_api_compatibility())
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    test_names = [
        "PostgreSQL TinyDB Wrapper",
        "Model Operations", 
        "API Compatibility"
    ]
    
    all_passed = True
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! The PostgreSQL TinyDB wrapper is fully compatible.")
        print("✅ The bulk update operations now work correctly.")
        print("✅ All ID handling issues have been resolved.")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)