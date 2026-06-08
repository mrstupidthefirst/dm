import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

print("Checking Supabase database contents...\n")

try:
    # Check users
    print("1️⃣  USERS:")
    users = supabase.table("users").select("id, username, email, role").execute()
    print(f"   Total: {len(users.data)} users")
    for user in users.data:
        print(f"   - ID: {user['id']}, Username: {user['username']}, Email: {user['email']}, Role: {user['role']}")
    
    # Check demandes
    print("\n2️⃣  DEMANDES:")
    demandes = supabase.table("demandes").select("*").execute()
    print(f"   Total: {len(demandes.data)} demandes")
    if demandes.data:
        for d in demandes.data:
            print(f"   - ID: {d['id']}, User: {d.get('user_id')}, Type: {d.get('type')}, Status: {d.get('statut')}")
    else:
        print("   ⚠️  NO DEMANDES FOUND - This is why the list is empty!")
    
    # Check entities
    print("\n3️⃣  ENTITIES:")
    entities = supabase.table("entities").select("*").execute()
    print(f"   Total: {len(entities.data)} entities")
    for e in entities.data:
        print(f"   - {e['name']}: {e.get('description')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
