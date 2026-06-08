import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

print("Testing Supabase connection...")
print(f"URL: {os.environ.get('SUPABASE_URL')}")
print(f"Key exists: {bool(os.environ.get('SUPABASE_KEY'))}")

try:
    # Test 1: Check if users table exists and is accessible
    print("\n1. Fetching users table...")
    response = supabase.table("users").select("id").limit(1).execute()
    print(f"   ✓ Users table is accessible. Records: {len(response.data)}")
    
    # Test 2: Check existing users
    print("\n2. Checking existing users...")
    existing = supabase.table("users").select("username, email").execute()
    print(f"   ✓ Found {len(existing.data)} users:")
    for user in existing.data:
        print(f"      - {user['username']} ({user['email']})")
    
    # Test 3: Check if entities table exists
    print("\n3. Fetching entities table...")
    entities = supabase.table("entities").select("name").execute()
    print(f"   ✓ Entities table is accessible. Records: {len(entities.data)}")
    
    # Test 4: Check if demandes table exists
    print("\n4. Fetching demandes table...")
    demandes = supabase.table("demandes").select("id").limit(1).execute()
    print(f"   ✓ Demandes table is accessible. Records: {len(demandes.data)}")
    
    print("\n✅ All tests passed! Supabase is working correctly.")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print("\nMake sure:")
    print("1. Your .env file has correct SUPABASE_URL and SUPABASE_KEY")
    print("2. Supabase tables are created (users, entities, demandes)")
    print("3. Your Supabase project is not in paused state")
