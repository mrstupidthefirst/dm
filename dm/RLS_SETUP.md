# 🔧 Supabase RLS Configuration Guide

## ❌ Problem: "Row Level Security" Blocking Inserts

Your Supabase tables have **Row Level Security (RLS)** enabled, which is blocking write operations. This is why signup/login fails.

## ✅ Solution: Disable RLS for Development

### Option 1: SQL Editor (Quickest)

1. Open Supabase Dashboard → Your Project
2. Go to **SQL Editor** (left sidebar)
3. Paste and run these commands:

```sql
-- Disable RLS on tables to allow public access
ALTER TABLE "public"."users" DISABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."entities" DISABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."demandes" DISABLE ROW LEVEL SECURITY;

-- Verify RLS is disabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('users', 'entities', 'demandes');
```

### Option 2: Via Supabase UI

1. Go to **Authentication** → **Policies** (left sidebar)
2. For each table:
   - Click table name
   - Click **RLS** toggle to disable
   - Or delete all existing policies

## 📝 After Disabling RLS

Run this command to populate initial data:

```bash
python init_supabase.py
```

Then test with these credentials:
- **Admin**: username: `admin_terminal1` / password: `admin123`
- **User**: username: `user1` / password: `user123`

## ⚠️ Security Note

Disabling RLS is fine for **development**, but for **production**, you should:
1. Set up proper RLS policies
2. Use Supabase Authentication
3. Create policies that check `auth.uid()`

Example production policy:
```sql
CREATE POLICY "Users can insert their own data"
  ON users FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);
```

## 🆘 Still Having Issues?

Check these:
1. ✓ `.env` file has correct SUPABASE_URL and SUPABASE_KEY
2. ✓ Supabase project is not in paused state
3. ✓ RLS is disabled on all tables
4. ✓ Tables exist: `users`, `entities`, `demandes`

Run this to verify:
```bash
python test_supabase.py
```
