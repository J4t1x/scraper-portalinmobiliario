#!/usr/bin/env python3
"""Check database schema"""
from database import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'properties' 
        ORDER BY ordinal_position
    """))
    
    print("\nColumnas en la tabla 'properties':")
    print("-" * 60)
    for row in result:
        print(f"{row.column_name:30} {row.data_type:20} {'NULL' if row.is_nullable == 'YES' else 'NOT NULL'}")
