-- scripts/db/001_enable_extensions.sql
/*
  Omni-Agent Database Extensions Initialization.

  Since we use SQLAlchemy and Alembic for table creation, this script ONLY
  contains the necessary database-level extensions that the ORM cannot create.
*/

-- Enable pgvector for semantic search and RAG capabilities (Long Term Memory)
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

-- Enable uuid-ossp for generating secure UUIDs as primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;
