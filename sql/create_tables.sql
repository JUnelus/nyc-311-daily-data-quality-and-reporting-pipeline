CREATE TABLE IF NOT EXISTS service_requests (
    unique_key INTEGER PRIMARY KEY,
    created_date TEXT NOT NULL,
    closed_date TEXT,
    agency TEXT,
    agency_name TEXT,
    complaint_type TEXT,
    descriptor TEXT,
    status TEXT,
    borough TEXT,
    incident_zip TEXT,
    latitude REAL,
    longitude REAL,
    loaded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

