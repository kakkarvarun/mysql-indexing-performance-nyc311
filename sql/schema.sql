-- Fresh, repeatable schema for NYC311 Assignment 5
-- We drop+create so reruns are clean and idempotent.

DROP TABLE IF EXISTS nyc311_stage;
CREATE TABLE nyc311_stage (
  created_date_txt         VARCHAR(64)  NULL,
  closed_date_txt          VARCHAR(64)  NULL,
  complaint_type           VARCHAR(255) NULL,
  descriptor               VARCHAR(1000) NULL,
  borough                  VARCHAR(64)  NULL,
  incident_zip             VARCHAR(32)  NULL,
  status                   VARCHAR(64)  NULL,
  resolution_description   TEXT         NULL,
  latitude_txt             VARCHAR(64)  NULL,
  longitude_txt            VARCHAR(64)  NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS nyc311;
CREATE TABLE nyc311 (
  id                       BIGINT AUTO_INCREMENT PRIMARY KEY,
  created_date             DATETIME NULL,
  closed_date              DATETIME NULL,
  complaint_type           VARCHAR(255) NULL,
  descriptor               VARCHAR(1000) NULL,
  borough                  VARCHAR(64) NULL,
  incident_zip             VARCHAR(32) NULL,
  status                   VARCHAR(64) NULL,
  resolution_description   TEXT NULL,
  latitude                 DECIMAL(9,6) NULL,
  longitude                DECIMAL(9,6) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- No indexes yet; we add them later in the assignment for before/after timings.
