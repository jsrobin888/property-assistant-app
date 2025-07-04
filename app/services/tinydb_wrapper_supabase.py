# supabase_tinydb_fixed.py
"""
FIXED: TinyDB wrapper for Supabase (Standard PostgreSQL)
Handles JSONB data type properly
"""

import os
import json
import threading
from typing import Dict, List, Optional, Any
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
    """TinyDB-compatible Query class - UNCHANGED"""
    
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

class QueryCondition:
    """Query condition class - UNCHANGED"""
    
    def __init__(self, path: List[str], operator: str, value: Any):
        self.path = path
        self.operator = operator
        self.value = value
    
    def __and__(self, other):
        return CombinedCondition(self, 'AND', other)
    
    def __or__(self, other):
        return CombinedCondition(self, 'OR', other)

class CombinedCondition:
    """Combined condition class - UNCHANGED"""
    
    def __init__(self, left, operator: str, right):
        self.left = left
        self.operator = operator
        self.right = right

class PostgreSQLTable:
    """PostgreSQL-backed table that mimics TinyDB Table API"""
    
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
        """Check if document matches condition"""
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
        """Insert multiple documents"""
        doc_ids = []
        for doc in documents:
            doc_ids.append(self.insert(doc))
        return doc_ids
    
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
    
    def update(self, fields: Dict, cond=None) -> List[int]:
        """Update documents - TinyDB compatible"""
        if cond is None:
            # Update all documents
            all_docs = self.all()
            doc_ids = [doc['doc_id'] for doc in all_docs]
        else:
            # Update matching documents
            matching_docs = self.search(cond)
            doc_ids = [doc['doc_id'] for doc in matching_docs]
        
        updated_ids = []
        
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    for doc_id in doc_ids:
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
    
    def remove(self, cond=None) -> List[int]:
        """Remove documents - TinyDB compatible"""
        if cond is None:
            # Remove all documents
            matching_docs = self.all()
        else:
            # Remove matching documents
            matching_docs = self.search(cond)
        
        doc_ids = [doc['doc_id'] for doc in matching_docs]
        
        if not doc_ids:
            return []
        
        with self._lock:
            conn = self._get_connection()
            try:
                with conn.cursor() as cur:
                    placeholders = ','.join(['%s' for _ in doc_ids])
                    cur.execute(f'DELETE FROM {self.table_name} WHERE doc_id IN ({placeholders})', doc_ids)
                    conn.commit()
            finally:
                self._return_connection(conn)
        
        return doc_ids
    
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
    
    def __len__(self) -> int:
        """Get table length"""
        return self.count()

class TinyDB:
    """PostgreSQL-backed TinyDB using standard PostgreSQL"""
    
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
    
    def update(self, fields: Dict, cond=None) -> List[int]:
        return self.default_table().update(fields, cond)
    
    def remove(self, cond=None) -> List[int]:
        return self.default_table().remove(cond)
    
    def count(self, cond=None) -> int:
        return self.default_table().count(cond)
    
    def close(self):
        """Close database connection pool"""
        if hasattr(self.connection_pool, 'closeall'):
            self.connection_pool.closeall()
    
    def __len__(self) -> int:
        return self.default_table().count()

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
    table_names = ['emails', 'replies', 'action_items', 'tenants', 'response_feedback', 'context_patterns', 'ai_responses']
    
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

def test_postgresql_connection():
    """Test PostgreSQL connection"""
    print("Testing PostgreSQL connection...")
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not set!")
        print("Set it with: export DATABASE_URL='postgresql://user:password@host:port/database'")
        return False
    
    try:
        # Create database connection
        db = TinyDB()
        
        # Test basic operations
        emails_table = db.table('emails')
        
        # Insert test data
        email_id = emails_table.insert({
            'id': str(uuid.uuid4()),
            'sender': 'test@example.com',
            'subject': 'Test Email',
            'body': 'This is a test email stored in PostgreSQL!',
            'status': 'unprocessed'
        })
        
        print(f"✅ Inserted email with doc_id: {email_id}")
        
        # Query data
        Email = Query()
        email = emails_table.get(Email.sender == 'test@example.com')
        
        if email:
            print(f"✅ Found email: {email['subject']}")
        else:
            print("❌ Could not find email")
        
        # Update data
        updated = emails_table.update({'status': 'processed'}, Email.sender == 'test@example.com')
        print(f"✅ Updated {len(updated)} emails")
        
        # Count data
        count = emails_table.count()
        print(f"✅ Total emails: {count}")
        
        # Get all emails
        all_emails = emails_table.all()
        print(f"✅ Retrieved {len(all_emails)} emails")
        
        print("\n🎉 PostgreSQL connection is working perfectly!")
        print("Your data is now stored in a standard PostgreSQL database!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("Make sure your DATABASE_URL is correct")
        return False

if __name__ == "__main__":
    test_postgresql_connection()