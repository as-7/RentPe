import psycopg2

regions = ["ap-south-1", "us-east-1", "ap-southeast-1", "eu-central-1", "us-west-1", "all"]

for region in regions:
    host = f"aws-0-{region}.pooler.supabase.com"
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres.hlwggvtdjdxeypdowftq",
            password="508798NNAKKI@dbrp",
            host=host,
            port="6543",
            connect_timeout=3
        )
        print(f"SUCCESS: {region}")
        conn.close()
        break
    except Exception as e:
        print(f"FAILED {region}: {e}")
