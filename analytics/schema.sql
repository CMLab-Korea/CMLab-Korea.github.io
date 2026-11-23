CREATE TABLE IF NOT EXISTS visitors (
  browser_id TEXT PRIMARY KEY,
  first_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visits (
  day TEXT NOT NULL,
  browser_id TEXT NOT NULL REFERENCES visitors(browser_id),
  country TEXT NOT NULL,
  path TEXT NOT NULL,
  PRIMARY KEY (day, browser_id, path)
);

CREATE INDEX IF NOT EXISTS visits_country ON visits(country, browser_id);
CREATE INDEX IF NOT EXISTS visits_path ON visits(path, browser_id);
