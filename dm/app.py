import os
import urllib.parse
import secrets
from functools import wraps
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)


def init_db():
    try:
        # Check if tables exist, if not create them
        # For Supabase, you typically create tables through the web console or migrations
        # This function ensures initial data is populated
        
        # Insert entities
        entities_data = [
            {"name": "terminal1", "description": "Port Terminal 1"},
            {"name": "douanes", "description": "Customs Department"},
            {"name": "marchandises", "description": "Merchandise Control"},
            {"name": "securite", "description": "Security Office"}
        ]
        
        for entity in entities_data:
            try:
                supabase.table("entities").insert(entity).execute()
            except:
                pass  # Entity might already exist
        
        # Insert default users
        users_data = [
            {"username": "admin_terminal1", "email": "admin1@portgate.com", "password": "admin123", "role": "admin", "entite": "terminal1"},
            {"username": "admin_douanes", "email": "admin2@portgate.com", "password": "admin123", "role": "admin", "entite": "douanes"},
            {"username": "user1", "email": "user1@gmail.com", "password": "user123", "role": "user", "entite": None},
            {"username": "user2", "email": "user2@gmail.com", "password": "user123", "role": "user", "entite": None}
        ]
        
        for user in users_data:
            try:
                supabase.table("users").insert(user).execute()
            except:
                pass  # User might already exist
        
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Veuillez vous connecter.", "error")
                return redirect(url_for("home"))
            if role and session.get("role") != role:
                flash("Acces non autorise.", "error")
                return redirect(url_for("home"))
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login/<role>", methods=["POST"])
def login(role):
    if role not in {"admin", "user"}:
        flash("Role invalide.", "error")
        return redirect(url_for("home"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        flash("Nom d'utilisateur et mot de passe requis.", "error")
        return redirect(url_for("home"))

    try:
        response = supabase.table("users").select("id, username, email, role, entite").eq("username", username).eq("password", password).execute()
        user = response.data[0] if response.data else None
    except Exception as e:
        print(f"Error during login: {e}")
        flash(f"Erreur de connexion a la base de donnees: {str(e)}", "error")
        return redirect(url_for("home"))

    if not user or user.get("role") != role:
        flash("Identifiants invalides pour ce type de connexion.", "error")
        return redirect(url_for("home"))

    session["user_id"] = user.get("id")
    session["username"] = user.get("username")
    session["email"] = user.get("email")
    session["role"] = user.get("role")

    if role == "admin":
        # Admin must select an entity
        return redirect(url_for("admin_select_entity"))
    
    session["entite"] = user.get("entite")
    return redirect(url_for("user_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Vous etes deconnecte.", "success")
    return redirect(url_for("home"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not all([username, email, password, confirm_password]):
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(url_for("signup"))

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caracteres.", "error")
            return redirect(url_for("signup"))

        # Check if email is valid (basic check)
        if "@" not in email or "." not in email:
            flash("Adresse email invalide.", "error")
            return redirect(url_for("signup"))

        try:
            # Check if username already exists
            existing_username = supabase.table("users").select("id").eq("username", username).execute()
            if existing_username.data:
                flash("Ce nom d'utilisateur existe deja.", "error")
                return redirect(url_for("signup"))
            
            # Check if email already exists
            existing_email = supabase.table("users").select("id").eq("email", email).execute()
            if existing_email.data:
                flash("Cet email existe deja.", "error")
                return redirect(url_for("signup"))
            
            # Insert new user
            response = supabase.table("users").insert({
                "username": username,
                "email": email,
                "password": password,
                "role": "user"
            }).execute()
            
            if response.data:
                flash("Compte cree avec succes. Vous pouvez maintenant vous connecter.", "success")
                return redirect(url_for("home"))
            else:
                flash("Erreur lors de la creation du compte.", "error")
                return redirect(url_for("signup"))
        except Exception as e:
            error_msg = str(e)
            print(f"Error during signup: {error_msg}")
            if "row-level security" in error_msg.lower() or "rls" in error_msg.lower() or "42501" in error_msg:
                flash("RLS bloquer. Desactiver RLS dans Supabase pour ce projet.", "error")
            elif "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                flash("Ce nom d'utilisateur ou email existe deja.", "error")
            else:
                flash(f"Erreur: {error_msg[:100]}", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")


@app.route("/admin/select-entity", methods=["GET", "POST"])
@login_required(role="admin")
def admin_select_entity():
    if request.method == "POST":
        selected_entity = request.form.get("entity", "").strip()
        
        if not selected_entity:
            flash("Veuillez selectionner une entite.", "error")
            return redirect(url_for("admin_select_entity"))

        # Verify entity exists
        try:
            response = supabase.table("entities").select("name").eq("name", selected_entity).execute()
            entity = response.data[0] if response.data else None
        except Exception as e:
            print(f"Error verifying entity: {e}")
            entity = None

        if not entity:
            flash("Entite invalide.", "error")
            return redirect(url_for("admin_select_entity"))

        session["entite"] = selected_entity
        flash(f"Vous travaillez maintenant sur l'entite: {selected_entity}", "success")
        return redirect(url_for("admin_dashboard"))

    # Get all available entities
    try:
        response = supabase.table("entities").select("name, description").order("name").execute()
        entities = [(entity["name"], entity["description"]) for entity in response.data]
    except Exception as e:
        print(f"Error fetching entities: {e}")
        entities = []

    return render_template("select_entity.html", entities=entities)


@app.route("/user/dashboard")
@login_required(role="user")
def user_dashboard():
    return render_template("user_home.html", username=session.get("username"))


@app.route("/user/cdemande", methods=["GET", "POST"])
@login_required(role="user")
def user_cdemande():
    if request.method == "POST":
        type_val = request.form.get("type_val", "").strip()
        entite_accueil = request.form.get("entite_accueil", "").strip()
        raison_entree = request.form.get("raison_entree", "").strip()
        nom_prenom = request.form.get("nom_prenom", "").strip()
        telephone = request.form.get("telephone", "").strip()
        piece_identite = request.form.get("piece_identite", "").strip()
        date_debut = request.form.get("date_debut", "").strip()
        date_fin = request.form.get("date_fin", "").strip()

        if not all(
            [
                type_val,
                entite_accueil,
                raison_entree,
                nom_prenom,
                telephone,
                piece_identite,
                date_debut,
                date_fin,
            ]
        ):
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for("user_cdemande"))

        try:
            supabase.table("demandes").insert({
                "user_id": session["user_id"],
                "type": type_val,
                "entite_accueil": entite_accueil,
                "raison_entree": raison_entree,
                "nom_prenom": nom_prenom,
                "telephone": telephone,
                "piece_identite": piece_identite,
                "date_debut": date_debut,
                "date_fin": date_fin,
                "statut": "en attente"
            }).execute()
            flash("Demande envoyee avec succes.", "success")
            return redirect(url_for("user_demandes"))
        except Exception as e:
            error_msg = str(e)
            print(f"Error creating demande: {error_msg}")
            if "row-level security" in error_msg.lower() or "42501" in error_msg:
                flash("RLS bloquer. Desactiver RLS dans Supabase.", "error")
            else:
                flash(f"Erreur: {error_msg[:100]}", "error")
            return redirect(url_for("user_cdemande"))

    return render_template("cdemande.html", username=session.get("username"))


@app.route("/user/demandes")
@login_required(role="user")
def user_demandes():
    try:
        response = supabase.table("demandes").select(
            "id, type, entite_accueil, raison_entree, nom_prenom, telephone, piece_identite, date_debut, date_fin, statut, motif_refus, created_at"
        ).eq("user_id", session["user_id"]).order("id", desc=True).execute()
        demandes = response.data

        # Check for new approvals
        approvals = supabase.table("demandes").select("id").eq("user_id", session["user_id"]).eq("statut", "approuve").eq("approval_seen", False).execute()
        has_new_approval = len(approvals.data) > 0

        if has_new_approval:
            supabase.table("demandes").update({"approval_seen": True}).eq("user_id", session["user_id"]).eq("statut", "approuve").eq("approval_seen", False).execute()
    except Exception as e:
        print(f"Error fetching demandes: {e}")
        demandes = []
        has_new_approval = False

    return render_template(
        "user_list.html",
        demandes=demandes,
        has_new_approval=has_new_approval,
        username=session.get("username"),
    )


@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    return render_template("list.html")


@app.route("/api/demandes")
@login_required(role="admin")
def api_get_demandes_admin():
    admin_entite = session.get("entite")
    try:
        response = supabase.table("demandes").select(
            "id, type, entite_accueil, raison_entree, nom_prenom, telephone, piece_identite, date_debut, date_fin, statut, created_at"
        ).eq("entite_accueil", admin_entite).order("id", desc=True).execute()
        records = response.data
    except Exception as e:
        print(f"Error fetching demandes: {e}")
        records = []

    demandes = []
    for record in records:
        demandes.append(
            {
                "id": record.get("id"),
                "type": record.get("type"),
                "entite_accueil": record.get("entite_accueil"),
                "raison_entree": record.get("raison_entree"),
                "nom_prenom": record.get("nom_prenom"),
                "telephone": record.get("telephone"),
                "photo": "",
                "piece_identite": record.get("piece_identite"),
                "date_debut": record.get("date_debut"),
                "date_fin": record.get("date_fin"),
                "statut": record.get("statut"),
                "created_at": record.get("created_at"),
            }
        )
    return jsonify({"success": True, "data": demandes})


@app.route("/api/demande/<int:demande_id>")
@login_required(role="admin")
def api_get_demande_admin(demande_id):
    admin_entite = session.get("entite")
    try:
        response = supabase.table("demandes").select(
            "id, type, entite_accueil, raison_entree, nom_prenom, telephone, piece_identite, date_debut, date_fin, statut, created_at"
        ).eq("id", demande_id).eq("entite_accueil", admin_entite).execute()
        record = response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching demande: {e}")
        record = None

    if not record:
        return jsonify({"success": False, "error": "Demande non trouvee"})

    demande = {
        "id": record.get("id"),
        "type": record.get("type"),
        "entite_accueil": record.get("entite_accueil"),
        "raison_entree": record.get("raison_entree"),
        "nom_prenom": record.get("nom_prenom"),
        "telephone": record.get("telephone"),
        "photo": "",
        "piece_identite": record.get("piece_identite"),
        "date_debut": record.get("date_debut"),
        "date_fin": record.get("date_fin"),
        "statut": record.get("statut"),
        "created_at": record.get("created_at"),
    }
    return jsonify({"success": True, "data": demande})


@app.route("/admin/demande/<int:demande_id>/status", methods=["POST"])
@login_required(role="admin")
def update_demande_status(demande_id):
    new_status = request.form.get("statut", "").strip().lower()
    motif_refus = request.form.get("motif_refus", "").strip()
    if new_status not in {"approved", "rejected"}:
        flash("Statut invalide.", "error")
        return redirect(url_for("admin_dashboard"))

    admin_entite = session.get("entite")
    try:
        response = supabase.table("demandes").select("id").eq("id", demande_id).eq("entite_accueil", admin_entite).execute()
        target = response.data[0] if response.data else None
    except Exception as e:
        print(f"Error checking demande: {e}")
        target = None

    if not target:
        flash("Demande introuvable pour votre entite.", "error")
        return redirect(url_for("admin_dashboard"))

    status_label = "approuve" if new_status == "approved" else "rejete"
    try:
        if status_label == "approuve":
            # generate (or regenerate) a secure QR token for this approved demande
            token = secrets.token_urlsafe(16)
            supabase.table("demandes").update({
                "statut": status_label,
                "motif_refus": motif_refus or None,
                "qr_code_unique": token
            }).eq("id", demande_id).execute()
        else:
            supabase.table("demandes").update({
                "statut": status_label,
                "motif_refus": motif_refus or None
            }).eq("id", demande_id).execute()
        flash("Statut mis a jour.", "success")
    except Exception as e:
        print(f"Error updating demande status: {e}")
        flash("Erreur lors de la mise a jour du statut.", "error")

    return redirect(url_for("admin_dashboard"))


@app.route("/user/card/<int:demande_id>")
@login_required(role="user")
def user_card(demande_id):
    try:
        response = supabase.table("demandes").select(
            "id, nom_prenom, entite_accueil, date_debut, date_fin, statut, qr_code_unique"
        ).eq("id", demande_id).eq("user_id", session["user_id"]).execute()
        demande = response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching demande: {e}")
        demande = None

    if not demande:
        flash("Demande introuvable.", "error")
        return redirect(url_for("user_demandes"))

    if demande.get("statut") != "approuve":
        flash("La carte est disponible uniquement pour les demandes approuvees.", "error")
        return redirect(url_for("user_demandes"))

    # Ensure a qr_code_unique exists for this approved demande; generate if missing
    token = demande.get("qr_code_unique")
    if not token:
        token = secrets.token_urlsafe(16)
        try:
            supabase.table("demandes").update({"qr_code_unique": token}).eq("id", demande_id).execute()
        except Exception as e:
            print(f"Error updating QR token: {e}")

    # Encode only the token in the QR (no URL)
    qr_payload = token

    qr_url = (
        "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data="
        + urllib.parse.quote(qr_payload)
    )
    return render_template("card.html", demande=demande, qr_url=qr_url)


@app.route("/verify-card/<int:demande_id>")
def verify_card(demande_id):
    try:
        response = supabase.table("demandes").select(
            "id, nom_prenom, entite_accueil, date_debut, date_fin, statut"
        ).eq("id", demande_id).eq("statut", "approuve").execute()
        demande = response.data[0] if response.data else None
    except Exception as e:
        print(f"Error verifying card: {e}")
        demande = None

    if not demande:
        return render_template("verify_card.html", demande=None, error="Demande introuvable ou non approuvée")
    
    return render_template("verify_card.html", demande=demande, error=None)


@app.route("/verify/<token>")
def verify_by_token(token):
    try:
        response = supabase.table("demandes").select(
            "id, nom_prenom, entite_accueil, date_debut, date_fin, statut"
        ).eq("qr_code_unique", token).eq("statut", "approuve").execute()
        demande = response.data[0] if response.data else None
    except Exception as e:
        print(f"Error verifying token: {e}")
        demande = None

    if not demande:
        return render_template("verify_card.html", demande=None, error="Demande introuvable ou non approuvée")
    return render_template("verify_card.html", demande=demande, error=None)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", debug=True)
