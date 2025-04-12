-- ========== BASE TABLES ==========

CREATE TABLE uploaded_trees (
    id BIGSERIAL PRIMARY KEY,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_filename VARCHAR,
    uploader_name VARCHAR,
    notes VARCHAR
);

CREATE TABLE individuals (
    id BIGSERIAL PRIMARY KEY,
    gedcom_id VARCHAR,
    tree_id BIGINT REFERENCES uploaded_trees(id),
    name VARCHAR NOT NULL,
    occupation VARCHAR,
    notes VARCHAR
);

CREATE INDEX ix_individuals_tree_gedcom ON individuals (tree_id, gedcom_id);

CREATE TABLE families (
    id SERIAL PRIMARY KEY,
    gedcom_id VARCHAR,
    tree_id BIGINT REFERENCES uploaded_trees(id),
    husband_id BIGINT REFERENCES individuals(id),
    wife_id BIGINT REFERENCES individuals(id),
    extra_details JSONB
);

CREATE INDEX ix_families_tree_gedcom ON families (tree_id, gedcom_id);

CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE,
    latitude FLOAT,
    longitude FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    historical_data JSONB
);

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR NOT NULL,
    date DATE,
    date_precision VARCHAR,
    notes VARCHAR,
    individual_id BIGINT REFERENCES individuals(id),
    family_id INTEGER REFERENCES families(id),
    location_id INTEGER REFERENCES locations(id),
    tree_id BIGINT REFERENCES uploaded_trees(id)
);

CREATE TABLE residence_history (
    id SERIAL PRIMARY KEY,
    individual_id BIGINT REFERENCES individuals(id),
    location_id INTEGER REFERENCES locations(id),
    start_date DATE,
    end_date DATE,
    notes VARCHAR
);

CREATE TABLE tree_versions (
    id SERIAL PRIMARY KEY,
    tree_name VARCHAR NOT NULL,
    version_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    diff_summary JSONB
);

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR,
    description VARCHAR,
    url VARCHAR
);

CREATE TABLE individual_sources (
    id SERIAL PRIMARY KEY,
    individual_id BIGINT REFERENCES individuals(id),
    source_id INTEGER REFERENCES sources(id),
    notes VARCHAR
);

CREATE TABLE user_actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action_type VARCHAR,
    context JSONB,
    decision VARCHAR,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tree_id BIGINT REFERENCES uploaded_trees(id)
);

CREATE TABLE tree_people (
    id SERIAL PRIMARY KEY,
    tree_id BIGINT REFERENCES uploaded_trees(id),
    first_name VARCHAR,
    last_name VARCHAR,
    full_name VARCHAR,
    birth_date DATE,
    death_date DATE,
    birth_location VARCHAR,
    death_location VARCHAR,
    gender VARCHAR,
    occupation VARCHAR,
    race VARCHAR,
    external_id VARCHAR,
    notes VARCHAR
);

CREATE TABLE tree_relationships (
    id SERIAL PRIMARY KEY,
    tree_id BIGINT REFERENCES uploaded_trees(id),
    person_id INTEGER,
    related_person_id INTEGER,
    relationship_type VARCHAR,
    notes VARCHAR
);
