def restore_db_from_excel():
    """Pulls all rows from grievance_backup.xlsx and re-inserts them into SQLite"""
    if os.path.exists(BACKUP_FILE):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            cursor = conn.cursor()
            df_backup = pd.read_excel(BACKUP_FILE)
            for _, row in df_backup.iterrows():
                cursor.execute("""
                    SELECT COUNT(*) FROM grievances 
                    WHERE grievant = ? AND occ_date = ? AND articles = ?
                """, (str(row.get("grievant", "")), str(row.get("occ_date", "")), str(row.get("articles", ""))))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO grievances (user_email, grievant, occ_date, articles, step, steward, committeeman, facts, remedy, evidence_image, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get("user_email", "")),
                        str(row.get("grievant", "")),
                        str(row.get("occ_date", "")),
                        str(row.get("articles", "")),
                        str(row.get("step", "")),
                        str(row.get("steward", "")),
                        str(row.get("committeeman", "")),
                        str(row.get("facts", "")),
                        str(row.get("remedy", "")),
                        str(row.get("evidence_image", "No Image")),
                        str(row.get("timestamp", datetime.now()))
                    ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error restoring from Excel: {e}")
            return False
    return False
