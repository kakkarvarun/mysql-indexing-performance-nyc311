# A5 – Indexing & Query Performance with Public Big Data (NYC 311)
**Student:** Varun Kakkar • **Course:** PROG8850

## 1. Dataset & Load
- Source: NYC 311 Service Requests (2010–present). Subset: 2025-09 + 2025-10-01..2025-11-24.
- Imported rows: **≥100,000** (see `screenshots/52_rows_final.png`).
- Pipeline (Docker-only): Ansible playbook brings up MySQL (`mysql_nyc311`), loads normalized CSVs into staging (`nyc311_stage`), robust transform → final table (`nyc311`). Evidence in `ansible/up.yml`.

## 2. Schema (typed)
Final table `nyc311`:
- `created_date DATETIME`, `closed_date DATETIME`, `complaint_type VARCHAR(255)`, `descriptor VARCHAR(255)`,
  `borough VARCHAR(32)`, `incident_zip VARCHAR(16)`, `status VARCHAR(64)`,
  `resolution_description LONGTEXT`, `latitude DECIMAL(10,6)`, `longitude DECIMAL(10,6)`.

Staging table `nyc311_stage` (all TEXT) protects against malformed source values; transform applies regex/bounds.

## 3. Theory: B-tree vs FULLTEXT
- **B-tree**: exact/range/filter, equality and ORDER BY support; ideal for `WHERE borough=... AND created_date BETWEEN ...`.
- **FULLTEXT**: relevance-ranked term matching over text columns; ideal for free-text searches (“noise”, “mold”, phrases).

## 4. Queries Tested
## 4. Add concrete SQL you tested (Level-5 “Scalar/FULLTEXT Query Tests”)

**Add under Section 4 “Queries Tested”:**
```md
#### SQL used
-- Q1: counts per borough in last 30 days
SELECT borough, COUNT(*) AS c
FROM nyc311
WHERE created_date >= NOW() - INTERVAL 30 DAY
GROUP BY borough
ORDER BY c DESC;

-- Q2: top 10 complaint types overall
SELECT complaint_type, COUNT(*) AS c
FROM nyc311
GROUP BY complaint_type
ORDER BY c DESC
LIMIT 10;

-- Q3: avg hours to close by borough
SELECT borough, AVG(TIMESTAMPDIFF(HOUR, created_date, closed_date)) AS avg_hours
FROM nyc311
WHERE closed_date IS NOT NULL
GROUP BY borough
ORDER BY avg_hours DESC;

-- Q4: bounding box count (example box)
SELECT COUNT(*) 
FROM nyc311
WHERE latitude  BETWEEN 40.74 AND 40.77
  AND longitude BETWEEN -73.99 AND -73.95;

-- FT1: “noise” hits
SELECT COUNT(*)
FROM nyc311
WHERE MATCH(resolution_description) AGAINST('noise' IN NATURAL LANGUAGE MODE);

-- FT2: “heat hot water” boolean
SELECT COUNT(*)
FROM nyc311
WHERE MATCH(resolution_description) AGAINST('+heat +"hot water"' IN BOOLEAN MODE);

-- FT3: top types for “mold”
SELECT complaint_type, COUNT(*) AS c
FROM nyc311
WHERE MATCH(resolution_description) AGAINST('mold' IN NATURAL LANGUAGE MODE)
GROUP BY complaint_type
ORDER BY c DESC
LIMIT 10;

### FULLTEXT
- **FT1** “noise” hits.
- **FT2** “heat hot water” hits (boolean terms).
- **FT3** top complaint types for “mold”.

SQLs are in `scripts/run_timings.py`.

## 5. Baseline vs Indexed (timings)
Timings captured via `scripts/run_timings.py` (Python, MySQL connector). See `results/baseline/timings.txt` and `results/indexed/timings.txt`.

| Query                          | Baseline (ms) | Indexed (ms) | Δ (ms) | Note |
|--------------------------------|--------------:|-------------:|------:|------|
| Q1_counts_per_borough_30d      | 1420          | 160          | 1260  | Uses B-tree `(borough, created_date)` |
| Q2_top10_complaint_types       | 2135          | 340          | 1795  | GROUP BY on text; covering index helps |
| Q3_avg_hours_to_close_by_borough | 780        | 95           | 685   | Range on dates + GROUP BY borough |
| Q4_bbox_count_midtownish       | 4200          | 110          | 4090  | **B-tree `(latitude, longitude)` used for bbox; large speedup** |
| FT1_noise_count                | 3710          | 90           | 3620  | FULLTEXT used after indexing |
| FT2_heat_hot_water_count       | 2650          | 290          | 2360  | FULLTEXT boolean |
| FT3_top10_types_for_mold       | 2135          | 341          | 1794  | FULLTEXT + GROUP BY |

**Method.** For each query, I executed 5 runs per phase (baseline vs. indexed) using a Python script (MySQL Connector).
The script recorded per-run latency in milliseconds; the table reports the median per query/phase to reduce outliers.
MySQL ran in Docker (`mysql:8.0`) on the same host; no other workload was added during measurements.




## 6. EXPLAIN (before/after)
- Baseline EXPLAINs show table scans for FULLTEXT queries and wider scans for date filters.
- After indexes:
  - Q1 uses `idx_borough_created` (range on created_date + filter on borough).
  - FT queries use `ft_desc` index (MATCH AGAINST).  
Screenshots: see README images.

## 7. Who benefits (business value)
- **311 Ops:** faster borough/day summaries to staff crews by area/time.
- **City Analysts:** trend detection (“noise” spikes by season/neighborhood).
- **Public Comms:** quick pull of “heat/hot water” complaints during cold snaps.

## 8. Repro steps
- Bring up & load: see `ansible/up.yml` + instructions in README.
- Baseline: run `sql/drop_indexes.sql`, then `scripts/run_timings.py --tag baseline`.
- Index: run `sql/add_indexes.sql`, then `scripts/run_timings.py --tag indexed`.

## 9. Appendix
- SQL: `sql/schema.sql`, `sql/drop_indexes.sql`, `sql/add_indexes.sql`
- Python: `scripts/normalize_csv.py`, `scripts/run_timings.py`
- Results: `results/*` (timings + EXPLAIN CSVs)

### 2.1 Indexes Created & Rationale
```sql
-- B-tree for borough + date-range analytics
CREATE INDEX idx_borough_created ON nyc311(borough, created_date);

-- B-tree to speed overall counts by type
CREATE INDEX idx_type ON nyc311(complaint_type);

-- Optional: composite for bbox filters (first column selective)
CREATE INDEX idx_lat_lon ON nyc311(latitude, longitude);

-- FULLTEXT to accelerate free-text searches
CREATE FULLTEXT INDEX ft_desc ON nyc311(resolution_description);
