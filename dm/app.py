import urllib.parse
from functools import wraps
import psycopg2
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"


def get_conn():
    return psycopg2.connect(
        database="flask_db",
        user="postgres",
        password="1111",
        host="localhost",
        port="5432",
    )


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(120) NOT NULL,
            role VARCHAR(20) NOT NULL,
            entite VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

   
    cur.execute(
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(120) UNIQUE
        """
    )
    cur.execute(
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS demandes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            type VARCHAR(50),
            entite_accueil VARCHAR(100),
            raison_entree TEXT,
            nom_prenom VARCHAR(100),
            telephone VARCHAR(20),
            piece_identite VARCHAR(50),
            date_debut DATE,
            date_fin DATE,
            statut VARCHAR(20) DEFAULT 'en attente',
            motif_refus TEXT,
            approval_seen BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        "ALTER TABLE demandes ADD COLUMN IF NOT EXISTS approval_seen BOOLEAN DEFAULT FALSE"
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entities (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT
        )
        """
    )

    cur.execute(
        """
        INSERT INTO entities (name, description)
        VALUES
            ('terminal1', 'Port Terminal 1'),
            ('douanes', 'Customs Department'),
            ('marchandises', 'Merchandise Control'),
            ('securite', 'Security Office')
        ON CONFLICT (name) DO NOTHING
        """
    )

    cur.execute(
        """
        INSERT INTO users (username, email, password, role, entite)
        VALUES
            ('admin_terminal1', 'admin1@portgate.com', 'admin123', 'admin', 'terminal1'),
            ('admin_douanes', 'admin2@portgate.com', 'admin123', 'admin', 'douanes'),
            ('user1', 'user1@gmail.com', 'user123', 'user', NULL),
            ('user2', 'user2@gmail.com', 'user123', 'user', NULL)
        ON CONFLICT (username) DO NOTHING
        """
    )

    conn.commit()
    cur.close()
    conn.close()


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

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, email, role, entite FROM users WHERE username = %s AND password = %s",
        (username, password),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or user[3] != role:
        flash("Identifiants invalides pour ce type de connexion.", "error")
        return redirect(url_for("home"))

    session["user_id"] = user[0]
    session["username"] = user[1]
    session["email"] = user[2]
    session["role"] = user[3]

    if role == "admin":
        # Admin must select an entity
        return redirect(url_for("admin_select_entity"))
    
    session["entite"] = user[4]
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

        conn = get_conn()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                INSERT INTO users (username, email, password, role)
                VALUES (%s, %s, %s, 'user')
                """,
                (username, email, password),
            )
            conn.commit()
            flash("Compte cree avec succes. Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for("home"))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Ce nom d'utilisateur ou email existe deja.", "error")
            return redirect(url_for("signup"))
        finally:
            cur.close()
            conn.close()

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
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT name FROM entities WHERE name = %s", (selected_entity,))
        entity = cur.fetchone()
        cur.close()
        conn.close()

        if not entity:
            flash("Entite invalide.", "error")
            return redirect(url_for("admin_select_entity"))

        session["entite"] = selected_entity
        flash(f"Vous travaillez maintenant sur l'entite: {selected_entity}", "success")
        return redirect(url_for("admin_dashboard"))

    # Get all available entities
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, description FROM entities ORDER BY name")
    entities = cur.fetchall()
    cur.close()
    conn.close()

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

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO demandes (
                user_id, type, entite_accueil, raison_entree, nom_prenom,
                telephone, piece_identite, date_debut, date_fin, statut, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'en attente', CURRENT_TIMESTAMP)
            """,
            (
                session["user_id"],
                type_val,
                entite_accueil,
                raison_entree,
                nom_prenom,
                telephone,
                piece_identite,
                date_debut,
                date_fin,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Demande envoyee avec succes.", "success")
        return redirect(url_for("user_demandes"))

    return render_template("cdemande.html", username=session.get("username"))


@app.route("/user/demandes")
@login_required(role="user")
def user_demandes():

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, type, entite_accueil, raison_entree, nom_prenom, telephone,
               piece_identite, date_debut, date_fin, statut, motif_refus, created_at
        FROM demandes
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],),
    )
    demandes = cur.fetchall()
    cur.execute(
        """
        SELECT COUNT(*) FROM demandes
        WHERE user_id = %s AND statut = 'approuve' AND approval_seen = FALSE
        """,
        (session["user_id"],),
    )
    has_new_approval = cur.fetchone()[0] > 0
    if has_new_approval:
        cur.execute(
            """
            UPDATE demandes
            SET approval_seen = TRUE
            WHERE user_id = %s AND statut = 'approuve' AND approval_seen = FALSE
            """,
            (session["user_id"],),
        )
        conn.commit()
    cur.close()
    conn.close()
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
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.id, d.type, d.entite_accueil, d.raison_entree, d.nom_prenom, d.telephone,
               '' as photo, d.piece_identite, d.date_debut, d.date_fin, d.statut, d.created_at
        FROM demandes d
        WHERE d.entite_accueil = %s
        ORDER BY d.id DESC
        """,
        (admin_entite,),
    )
    records = cur.fetchall()
    cur.close()
    conn.close()

    demandes = []
    for record in records:
        demandes.append(
            {
                "id": record[0],
                "type": record[1],
                "entite_accueil": record[2],
                "raison_entree": record[3],
                "nom_prenom": record[4],
                "telephone": record[5],
                "photo": record[6],
                "piece_identite": record[7],
                "date_debut": str(record[8]) if record[8] else None,
                "date_fin": str(record[9]) if record[9] else None,
                "statut": record[10],
                "created_at": str(record[11]) if record[11] else None,
            }
        )
    return jsonify({"success": True, "data": demandes})


@app.route("/api/demande/<int:demande_id>")
@login_required(role="admin")
def api_get_demande_admin(demande_id):
    admin_entite = session.get("entite")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, type, entite_accueil, raison_entree, nom_prenom, telephone,
               '' as photo, piece_identite, date_debut, date_fin, statut, created_at
        FROM demandes
        WHERE id = %s AND entite_accueil = %s
        """,
        (demande_id, admin_entite),
    )
    record = cur.fetchone()
    cur.close()
    conn.close()

    if not record:
        return jsonify({"success": False, "error": "Demande non trouvee"})

    demande = {
        "id": record[0],
        "type": record[1],
        "entite_accueil": record[2],
        "raison_entree": record[3],
        "nom_prenom": record[4],
        "telephone": record[5],
        "photo": record[6],
        "piece_identite": record[7],
        "date_debut": str(record[8]) if record[8] else None,
        "date_fin": str(record[9]) if record[9] else None,
        "statut": record[10],
        "created_at": str(record[11]) if record[11] else None,
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
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM demandes WHERE id = %s AND entite_accueil = %s",
        (demande_id, admin_entite),
    )
    target = cur.fetchone()
    if not target:
        cur.close()
        conn.close()
        flash("Demande introuvable pour votre entite.", "error")
        return redirect(url_for("admin_dashboard"))

    status_label = "approuve" if new_status == "approved" else "rejete"
    cur.execute(
        """
        UPDATE demandes
        SET statut = %s,
            motif_refus = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (status_label, motif_refus or None, demande_id),
    )
    conn.commit()
    cur.close()
    conn.close()

    flash("Statut mis a jour.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/user/card/<int:demande_id>")
@login_required(role="user")
def user_card(demande_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nom_prenom, entite_accueil, date_debut, date_fin, statut
        FROM demandes
        WHERE id = %s AND user_id = %s
        """,
        (demande_id, session["user_id"]),
    )
    demande = cur.fetchone()
    cur.close()
    conn.close()

    if not demande:
        flash("Demande introuvable.", "error")
        return redirect(url_for("user_demandes"))

    if demande[5] != "approuve":
        flash("La carte est disponible uniquement pour les demandes approuvees.", "error")
        return redirect(url_for("user_demandes"))

    qr_payload = url_for("verify_card", demande_id=demande[0], _external=True)
    qr_url = (
        "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data="
        + urllib.parse.quote(qr_payload)
    )
    return render_template("card.html", demande=demande, qr_url=qr_url)


@app.route("/verify-card/<int:demande_id>")
def verify_card(demande_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nom_prenom, entite_accueil, date_debut, date_fin, statut
        FROM demandes
        WHERE id = %s AND statut = 'approuve'
        """,
        (demande_id,),
    )
    demande = cur.fetchone()
    cur.close()
    conn.close()

    if not demande:
        return render_template("verify_card.html", demande=None, error="Demande introuvable ou non approuvée")
    
    return render_template("verify_card.html", demande=demande, error=None)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
