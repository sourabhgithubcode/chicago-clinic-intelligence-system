import pytds

print("Testing connection...")

try:
    # Try with TDS 7.4 which should auto-enable encryption for Azure
    conn = pytds.connect(
        server='srodagi.database.windows.net',
        database='clinic-intelligence-db',
        user='CloudSA6ec5ad8f',
        password='Sagardagar@21212',
        port=1433,
        tds_version='7.4',
        use_mars=False
    )
    print("✅ SUCCESS!")

    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    print(f"Connected to: {version[:80]}")

    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPytds doesn't support Azure SQL encryption.")
    print("\n💡 Solutions:")
    print("1. Use Azure PostgreSQL (your $200 student credit covers it)")
    print("2. Connect via DB Browser for SQLite GUI tool instead")
    print("3. Use Azure Data Studio (Microsoft's free tool)")
