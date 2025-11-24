import os, time, json, csv, argparse
import mysql.connector as mysql
from tabulate import tabulate
from pathlib import Path

QUERIES_SCALAR = [
  ("Q1_counts_per_borough_30d",
   """SELECT borough, COUNT(*) AS cnt
      FROM nyc311
      WHERE created_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
      GROUP BY borough ORDER BY cnt DESC;"""),
  ("Q2_top10_complaint_types",
   """SELECT complaint_type, COUNT(*) AS cnt
      FROM nyc311 GROUP BY complaint_type
      ORDER BY cnt DESC LIMIT 10;"""),
  ("Q3_avg_hours_to_close_by_borough",
   """SELECT borough, AVG(TIMESTAMPDIFF(HOUR, created_date, closed_date)) AS avg_hours
      FROM nyc311 WHERE closed_date IS NOT NULL
      GROUP BY borough ORDER BY avg_hours DESC;"""),
  ("Q4_bbox_count_midtownish",
   """SELECT COUNT(*) AS cnt
      FROM nyc311
      WHERE latitude BETWEEN 40.5 AND 41
        AND longitude BETWEEN -74.5 AND -73.5;"""),
]

QUERIES_FT = [
  ("FT1_noise_count",
   """SELECT COUNT(*) AS cnt
      FROM nyc311
      WHERE MATCH(complaint_type, descriptor, resolution_description)
            AGAINST('+noise' IN BOOLEAN MODE);"""),
  ("FT2_heat_hot_water_count",
   """SELECT COUNT(*) AS cnt
      FROM nyc311
      WHERE MATCH(complaint_type, descriptor, resolution_description)
            AGAINST('+heat +hot +water' IN BOOLEAN MODE);"""),
  ("FT3_top10_types_for_mold",
   """SELECT complaint_type, COUNT(*) AS cnt
      FROM nyc311
      WHERE MATCH(complaint_type, descriptor, resolution_description)
            AGAINST('+mold' IN BOOLEAN MODE)
      GROUP BY complaint_type
      ORDER BY cnt DESC LIMIT 10;"""),
]

def run_query(cnx, sql):
    cur = cnx.cursor(dictionary=True)
    t0 = time.perf_counter()
    cur.execute(sql)
    rows = cur.fetchall()
    ms = (time.perf_counter() - t0) * 1000.0
    cur.close()
    return rows, ms

def explain_query(cnx, sql):
    cur = cnx.cursor(dictionary=True)
    cur.execute("EXPLAIN " + sql)
    rows = cur.fetchall()
    cur.close()
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="baseline or indexed")
    ap.add_argument("--host", default=os.getenv("DB_HOST","mysql_nyc311"))
    ap.add_argument("--port", type=int, default=int(os.getenv("DB_PORT","3306")))
    ap.add_argument("--db", default=os.getenv("DB_NAME","nyc311_db"))
    ap.add_argument("--user", default=os.getenv("DB_USER","app_user"))
    ap.add_argument("--password", default=os.getenv("DB_PASS","app_password"))
    args = ap.parse_args()

    outdir = Path("results") / args.tag
    outdir.mkdir(parents=True, exist_ok=True)

    cnx = mysql.connect(
        host=args.host, port=args.port, database=args.db,
        user=args.user, password=args.password,
        autocommit=True
    )

    allq = [("scalar", q) for q in QUERIES_SCALAR] + [("fulltext", q) for q in QUERIES_FT]
    table_rows = []
    for qtype, (name, sql) in allq:
        rows, ms = run_query(cnx, sql)
        table_rows.append({"name": name, "type": qtype, "ms": round(ms,2), "rows": len(rows)})

        # Save result sample (first 20 rows) for evidence
        with open(outdir / f"{name}_sample.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if rows:
                w.writerow(rows[0].keys())
                for r in rows[:20]:
                    w.writerow([r[k] for k in rows[0].keys()])

        # Save EXPLAIN
        exp = explain_query(cnx, sql)
        with open(outdir / f"explain_{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if exp:
                w.writerow(exp[0].keys())
                for r in exp:
                    w.writerow([r[k] for k in exp[0].keys()])

    cnx.close()

    # Write timings table CSV + pretty txt
    with open(outdir / "timings.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name","type","ms","rows"])
        w.writeheader()
        w.writerows(table_rows)

    with open(outdir / "timings.txt", "w", encoding="utf-8") as f:
        f.write(tabulate(table_rows, headers="keys", tablefmt="github"))

    with open(outdir / "timings.json", "w", encoding="utf-8") as f:
        json.dump(table_rows, f, indent=2)

if __name__ == "__main__":
    main()
