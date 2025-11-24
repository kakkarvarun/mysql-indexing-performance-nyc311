# NYC311 Indexing & Query Performance (MySQL + Docker)

**Student:** Varun Kakkar • **Course:** PROG8850 • **Assignment 5**

This repo loads a ≥100k-row slice of the **NYC 311 Service Requests** dataset into MySQL, runs **baseline** vs **indexed** queries (scalar + FULLTEXT), captures **timings** and **EXPLAIN**, and documents the outcomes.

---

## Project structure
ansible/ # Ansible control (containerized) to bring up MySQL + load data
sql/ # schema + index scripts
scripts/ # normalize_csv.py + run_timings.py (writes results/*)
data/ # local CSVs (not committed due to size)
results/ # baseline/ and indexed/ timings + EXPLAIN CSVs/JSON
screenshots/ # evidence for rubric


---

## Quick start (Windows PowerShell)
1. **Build Ansible control image**
   ```powershell
   docker build -t a5/ansiblectl:latest ansible

2. Bring up MySQL + create schema + load CSVs (staging → final)
docker run --rm `
  -v /var/run/docker.sock:/var/run/docker.sock `
  -v "$(Get-Location):/work" `
  -e HOST_REPO=/work `
  -w /work `
  a5/ansiblectl:latest ansible-playbook ansible/up.yml -i ansible/hosts.ini

Verify tables and counts:
docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db -e "SHOW TABLES;"
docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db -e "SELECT COUNT(*) AS rows_in_final FROM nyc311;"
docker ps

Baseline vs Indexed workflow
1) Baseline (drop indexes first)

Get-Content .\sql\drop_indexes.sql | docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db
docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db -e "SHOW INDEX FROM nyc311\G"

Run timings:

docker run --rm --network nyc311_net `
  -v "$(Get-Location):/work" -w /work `
  python:3.11-slim bash -lc "pip install -r requirements.txt && python scripts/run_timings.py --tag baseline"


Artifacts appear in results/baseline/:


2) Add indexes (B-tree + FULLTEXT)

Get-Content .\sql\add_indexes.sql | docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db
docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db -e "SHOW INDEX FROM nyc311\G"

Re-run timings:

docker run --rm --network nyc311_net `
  -v "$(Get-Location):/work" -w /work `
  python:3.11-slim bash -lc "pip install -r requirements.txt && python scripts/run_timings.py --tag indexed"

Indexed artifacts in results/indexed/:

Queries covered (see scripts/run_timings.py)

Scalar: counts per borough (30d), top 10 complaint types, avg hours to close by borough, bounding-box count.

FULLTEXT: noise, "heat hot water" (boolean), top complaint types for mold.

For EXPLAIN evidence:

# Q1 (scalar)
docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db -e "EXPLAIN FORMAT=JSON SELECT borough, COUNT(*) FROM nyc311 WHERE created_date >= NOW() - INTERVAL 30 DAY GROUP BY borough;" > results/baseline/explain_q1.json
docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db -e "EXPLAIN FORMAT=JSON SELECT borough, COUNT(*) FROM nyc311 WHERE created_date >= NOW() - INTERVAL 30 DAY GROUP BY borough;" > results/indexed/explain_q1.json

# FT1 (FULLTEXT on resolution_description)
docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db -e "EXPLAIN FORMAT=JSON SELECT COUNT(*) FROM nyc311 WHERE MATCH(resolution_description) AGAINST('noise' IN NATURAL LANGUAGE MODE);" > results/baseline/explain_ft1.json
docker exec -i mysql_nyc311 mysql -uapp_user -papp_password nyc311_db -e "EXPLAIN FORMAT=JSON SELECT COUNT(*) FROM nyc311 WHERE MATCH(resolution_description) AGAINST('noise' IN NATURAL LANGUAGE MODE);" > results/indexed/explain_ft1.json


Findings (how indexing changed performance)

See results/baseline/timings.csv vs results/indexed/timings.csv for your exact numbers. At a high level:

B-tree (borough, created_date) turns borough-by-date summaries from table scans into index-range scans.

FULLTEXT on resolution_description converts slow LIKE scans into fast, ranked text search.

