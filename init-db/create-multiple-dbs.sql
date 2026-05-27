SELECT 'CREATE DATABASE typerrdb'
    WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'typerrdb'
)\gexec

SELECT 'CREATE DATABASE typerrdb_mlflow'
    WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'typerrdb_mlflow'
)\gexec