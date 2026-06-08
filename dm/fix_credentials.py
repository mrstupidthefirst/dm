#!/usr/bin/env python3
"""
Helper script to update Supabase credentials
"""

print("=" * 60)
print("SUPABASE CREDENTIALS FIX")
print("=" * 60)

print("\n📍 STEP 1: Get your correct API keys from Supabase")
print("\n1. Go to: https://app.supabase.com")
print("2. Select your project (qajusctuthefnsigbeyj)")
print("3. Click Settings → API (bottom left)")
print("4. Find these values:")
print("   - Project URL (starts with https://)")
print("   - anon public (starts with eyJ...)")
print("\n⚠️  DO NOT use 'sb_publishable_' key - that's wrong!\n")

url = input("Enter SUPABASE_URL: ").strip()
key = input("Enter SUPABASE_KEY (anon public): ").strip()

if not url or not key:
    print("❌ Error: Both URL and KEY are required!")
    exit(1)

if not url.startswith("https://"):
    print("❌ Error: URL should start with https://")
    exit(1)

if key.startswith("sb_publishable_"):
    print("⚠️  Warning: You entered the publishable key!")
    print("   This won't work. Use the 'anon public' key instead.")
    exit(1)

# Update .env file
try:
    with open(".env", "w") as f:
        f.write(f"SUPABASE_URL={url}\n")
        f.write(f"SUPABASE_KEY={key}\n")
    print("\n✅ SUCCESS! .env file updated.")
    print("\nYour .env now contains:")
    print(f"  SUPABASE_URL={url}")
    print(f"  SUPABASE_KEY={key[:20]}...")
    print("\n🚀 Now run: python app.py")
except Exception as e:
    print(f"❌ Error writing .env: {e}")
    exit(1)
