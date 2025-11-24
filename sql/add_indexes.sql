-- B-tree indexes
CREATE INDEX idx_borough_created ON nyc311 (borough, created_date);
CREATE INDEX idx_created ON nyc311 (created_date);

-- FULLTEXT index over 3 text columns
CREATE FULLTEXT INDEX ft_desc
  ON nyc311 (complaint_type, descriptor, resolution_description);
