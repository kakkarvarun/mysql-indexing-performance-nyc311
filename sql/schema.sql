-- sql/schema.sql

DROP TABLE IF EXISTS nyc311_stage;
CREATE TABLE nyc311_stage (
  created_date_txt           VARCHAR(64),
  closed_date_txt            VARCHAR(64),
  complaint_type             TEXT,
  descriptor                 TEXT,
  borough                    VARCHAR(32),
  incident_zip               VARCHAR(16),
  status                     VARCHAR(64),
  resolution_description     LONGTEXT,
  latitude_txt               VARCHAR(64),
  longitude_txt              VARCHAR(64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS nyc311;
CREATE TABLE nyc311 (
  id                         BIGINT AUTO_INCREMENT PRIMARY KEY,
  created_date               DATETIME NULL,
  closed_date                DATETIME NULL,
  complaint_type             VARCHAR(255),
  descriptor                 VARCHAR(255),
  borough                    VARCHAR(32),
  incident_zip               VARCHAR(16),
  status                     VARCHAR(64),
  resolution_description     LONGTEXT,
  latitude                   DECIMAL(10,6) NULL,
  longitude                  DECIMAL(10,6) NULL,
  KEY idx_borough_created (borough, created_date),
  KEY idx_created (created_date),
  FULLTEXT KEY ft_desc (complaint_type, descriptor, resolution_description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
