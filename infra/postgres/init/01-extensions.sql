-- Runs once, only when the data directory is first initialized.
--
-- The vector extension needs superuser rights, which a managed Postgres may not
-- grant to the application role. Enabling it here keeps local development ready
-- before any migration runs. Task 2.5 must also handle it for environments that
-- are not built from this compose file.
CREATE EXTENSION IF NOT EXISTS vector;
