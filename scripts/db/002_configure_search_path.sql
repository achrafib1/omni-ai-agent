-- scripts/db/002_configure_search_path.sql
/*
  Database Schema Isolation and Search Path Configuration.

  This script registers the isolated 'omni' schema namespace and binds
  the database's search path so that our agent can resolve the 'pgvector'
  extension installed in the 'public' schema.
*/

-- 1. Create the isolated schema namespace
CREATE SCHEMA IF NOT EXISTS omni;

-- 2. Bind the search path for our database user (default is 'postgres')
-- This is critical. It allows pgvector (in public) to work seamlessly with our tables (in omni)
ALTER ROLE postgres SET search_path TO omni, public;

-- Also apply to the current session so migrations can run instantly
SET search_path TO omni, public;
