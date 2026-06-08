import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

print("Initializing database with sample data...")

try:
    # Insert entities
    print("\n1. Adding entities...")
    entities_data = [
        {"name": "terminal1", "description": "Port Terminal 1"},
        {"name": "douanes", "description": "Customs Department"},
        {"name": "marchandises", "description": "Merchandise Control"},
        {"name": "securite", "description": "Security Office"}
    ]
    
    for entity in entities_data:
        try:
            supabase.table("entities").insert(entity).execute()
            print(f"   ✓ Added entity: {entity['name']}")
        except Exception as e:
            print(f"   ⚠ Entity {entity['name']} might already exist: {e}")
    
    # Insert default users
    print("\n2. Adding default users...")
    users_data = [
        {"username": "admin_terminal1", "email": "admin1@portgate.com", "password": "admin123", "role": "admin", "entite": "terminal1"},
        {"username": "admin_douanes", "email": "admin2@portgate.com", "password": "admin123", "role": "admin", "entite": "douanes"},
        {"username": "user1", "email": "user1@gmail.com", "password": "user123", "role": "user", "entite": None},
        {"username": "user2", "email": "user2@gmail.com", "password": "user123", "role": "user", "entite": None}
    ]
    
    for user in users_data:
        try:
            supabase.table("users").insert(user).execute()
            print(f"   ✓ Added user: {user['username']} ({user['email']})")
        except Exception as e:
            print(f"   ⚠ User {user['username']} might already exist: {e}")
    
    print("\n✅ Database initialization complete!")
    print("\n📝 Test credentials:")
    print("   Admin: admin_terminal1 / admin123")
    print("   User: user1 / user123")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
