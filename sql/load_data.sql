LOAD DATA INFILE '/import/nyc311_q1_2024.csv'
INTO TABLE nyc311
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@created_date,@closed_date,complaint_type,descriptor,borough,incident_zip,status,resolution_description,latitude,longitude)
SET
  created_date = NULLIF(STR_TO_DATE(@created_date, '%Y-%m-%dT%H:%i:%s.%f'), ''),
  closed_date  = NULLIF(STR_TO_DATE(@closed_date,  '%Y-%m-%dT%H:%i:%s.%f'), '');
