-- ==============================================================================
-- FashXStudio: Local PostgreSQL Initialization Script
-- Initializes dedicated test database if not already present
-- ==============================================================================

SELECT 'CREATE DATABASE fashion_test'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'fashion_test'
)\gexec

GRANT ALL PRIVILEGES ON DATABASE fashion_test TO fashion;
