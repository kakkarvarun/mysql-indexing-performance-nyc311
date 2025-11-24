import os, time, csv
import mysql.connector as mysql

DB_HOST = os.getenv("DB_HOST", "mysql_nyc311")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "nyc311_db")
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASS = os.getenv("DB_PASS", "app_password")

OUT_TAG = os.getenv("TAG", None)

def connect():
    return mysql.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME
    )

def run_query(cnx, sql):
    cur = cnx.cursor()
    t0 = time.perf_counter()
    cur.execute(sql)
    rows = cur.fetchall()
    ms = (time.perf_counter() - t0) * 1000.0
    cur.close()
    return rows, ms

def explain(cnx, sql):
    cur = cnx.cursor()
    cur.execute("EXPLAIN " + sql)
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    cur.close()
    return headers, rows

def write_csv(path, headers, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if headers: w.writerow(headers)
        for r in rows: w.writerow(r)

def has_fulltext_on_descriptor(cnx):
    sql = """
    SELECT COUNT(*) 
    FROM information_schema.statistics 
    WHERE table_schema = %s 
      AND table_name = 'nyc311'
      AND index_type = 'FULLTEXT'
      AND column_name = 'descriptor'
    """
    cur = cnx.cursor()
    cur.execute(sql, (DB_NAME,))
    n = cur.fetchone()[0]
    cur.close()
    return n > 0

def main():
    tag = OUT_TAG
    # allow CLI flag too: --tag baseline
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--tag", default=tag)
    args = p.parse_args()
    tag = args.tag or "run"

    out_dir = os.path.join("results", tag)
    os.makedirs(out_dir, exist_ok=True)

    cnx = connect()

    # Q1: Counts per borough (last 30 days)
    q1 = """
    SELECT borough, COUNT(*) AS cnt
    FROM nyc311
    WHERE created_date >= NOW() - INTERVAL 30 DAY
    GROUP BY borough
    ORDER BY cnt DESC
    """
    rows, ms = run_query(cnx, q1)
    write_csv(os.path.join(out_dir, "Q1_counts_per_borough_30d.csv"), ["borough","cnt"], rows)
    h, xr = explain(cnx, q1)
    write_csv(os.path.join(out_dir, "explain_Q1_counts_per_borough_30d.csv"), h, xr)

    # FT1: Noise/music complaints
    ft_available = has_fulltext_on_descriptor(cnx)
    if ft_available:
        ft_label = "fulltext"
        ft_sql = """SELECT COUNT(*) 
                    FROM nyc311 
                    WHERE MATCH(descriptor) AGAINST('+noise +music' IN BOOLEAN MODE)"""
    else:
        ft_label = "like"
        ft_sql = """SELECT COUNT(*)
                    FROM nyc311
                    WHERE (descriptor LIKE '%noise%' OR descriptor LIKE '%music%')"""

    rows, ms_ft = run_query(cnx, ft_sql)
    write_csv(os.path.join(out_dir, f"FT1_noise_{ft_label}.csv"), ["count"], rows)
    h, xr = explain(cnx, ft_sql)
    write_csv(os.path.join(out_dir, f"explain_FT1_noise_{ft_label}.csv"), h, xr)

    # Simple timings summary
    write_csv(os.path.join(out_dir, "timings.csv"),
              ["query","mode","ms"],
              [["Q1_counts_per_borough_30d","b-tree/none", f"{ms:.2f}"],
               ["FT1_noise", ft_label, f"{ms_ft:.2f}"]])

    print(f"Done. Results in {out_dir}")
    cnx.close()

if __name__ == "__main__":
    main()
