CREATE TABLE IF NOT EXISTS nyc311 (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_date DATETIME NULL,
  closed_date   DATETIME NULL,
  complaint_type VARCHAR(100) NULL,
  descriptor     TEXT NULL,
  borough        VARCHAR(30) NULL,
  incident_zip   VARCHAR(10) NULL,
  status         VARCHAR(40) NULL,
  resolution_description TEXT NULL,
  latitude   DECIMAL(10,6) NULL,
  longitude  DECIMAL(10,6) NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
