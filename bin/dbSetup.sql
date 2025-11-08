-- Ensure SCRAM, and create/alter the application role
SET password_encryption = 'scram-sha-256';

DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'photo_svc') THEN
        CREATE ROLE photo_svc LOGIN PASSWORD '5cB84m6GgUOyeTZWXsdB08wd6drdadKi-1_GYOCJrX0';
    ELSE
        ALTER ROLE photo_svc WITH LOGIN PASSWORD '5cB84m6GgUOyeTZWXsdB08wd6drdadKi-1_GYOCJrX0';
    END IF;
END
$$;

-- Create the database if it doesn't exist (psql-only \gexec trick; no dblink needed)
SELECT 'CREATE DATABASE clever_photos_service WITH OWNER photo_svc ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'clever_photos_service')\gexec

-- Switch to the new database to set schema ownership/privs there
\connect clever_photos_service

ALTER SCHEMA public OWNER TO photo_svc;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO photo_svc;
