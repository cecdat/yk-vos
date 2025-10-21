-- init_schema.sql for yk-vos-v3
CREATE TABLE IF NOT EXISTS vos_instances (
  id SERIAL PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  base_url VARCHAR(256) NOT NULL,
  description TEXT,
  enabled BOOLEAN DEFAULT TRUE,
  api_user VARCHAR(128),
  api_password VARCHAR(128)
);

CREATE TABLE IF NOT EXISTS phones (
  id SERIAL PRIMARY KEY,
  e164 VARCHAR(64),
  status VARCHAR(64),
  last_seen TIMESTAMP DEFAULT now(),
  vos_id INTEGER
);

CREATE TABLE IF NOT EXISTS phone_stats (
  id SERIAL PRIMARY KEY,
  vos_id INTEGER,
  metric VARCHAR(64),
  value INTEGER,
  ts TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cdrs (
  id SERIAL PRIMARY KEY,
  vos_id INTEGER,
  caller VARCHAR(64),
  callee VARCHAR(64),
  start_time TIMESTAMP,
  duration INTEGER,
  cost NUMERIC(10,4),
  disposition VARCHAR(32),
  raw TEXT
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(64) UNIQUE NOT NULL,
  hashed_password VARCHAR(256) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE
);
