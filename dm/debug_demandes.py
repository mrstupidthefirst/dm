import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

print("Testing user_demandes query...\n")

# Test for user_id = 3 (user1)
user_id = 3

try:
    response = supabase.table("demandes").select(
        "id, type, entite_accueil, raison_entree, nom_prenom, telephone, piece_identite, date_debut, date_fin, statut, motif_refus, created_at"
    ).eq("user_id", user_id).order("id", desc=True).execute()
    
    print(f"✅ Query successful for user_id={user_id}")
    print(f"Total demandes: {len(response.data)}")
    
    if response.data:
        print("\nData returned:")
        for d in response.data:
            print(f"\n  ID: {d.get('id')}")
            print(f"  Type: {d.get('type')}")
            print(f"  Entite: {d.get('entite_accueil')}")
            print(f"  Raison: {d.get('raison_entree')}")
            print(f"  Nom: {d.get('nom_prenom')}")
            print(f"  Telephone: {d.get('telephone')}")
            print(f"  Piece: {d.get('piece_identite')}")
            print(f"  Dates: {d.get('date_debut')} -> {d.get('date_fin')}")
            print(f"  Status: {d.get('statut')}")
    else:
        print("❌ No demandes found for this user!")
    
except Exception as e:
    print(f"❌ Error: {e}")
