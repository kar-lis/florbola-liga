from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "florbols67"
fails = "florbols.db"

def get_db():
    conn = sqlite3.connect(fails, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def izveidot_db():
    conn = get_db()
    c = conn.cursor()
    


    c.executescript("""
        CREATE TABLE IF NOT EXISTS ligas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nosaukums TEXT NOT NULL,
            sezona    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS komandas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nosaukums TEXT NOT NULL,
            liga_id   INTEGER NOT NULL,
            FOREIGN KEY (liga_id) REFERENCES ligas(id)
        );

        CREATE TABLE IF NOT EXISTS speles (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            liga_id            INTEGER NOT NULL,
            majas_komanda_id   INTEGER NOT NULL,
            viesi_komanda_id   INTEGER NOT NULL,
            majas_varti        INTEGER NOT NULL DEFAULT 0,
            viesi_varti        INTEGER NOT NULL DEFAULT 0,
            datums             TEXT NOT NULL,
            FOREIGN KEY (liga_id)          REFERENCES ligas(id),
            FOREIGN KEY (majas_komanda_id) REFERENCES komandas(id),
            FOREIGN KEY (viesi_komanda_id) REFERENCES komandas(id)
        );

       CREATE TABLE IF NOT EXISTS lietotaji (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        vards         TEXT NOT NULL,
        lietotajvards TEXT NOT NULL UNIQUE,
        loma          TEXT NOT NULL DEFAULT 'skatitajs',
        parole_hash   TEXT NOT NULL,
        liga_id       INTEGER,
        FOREIGN KEY (liga_id) REFERENCES ligas(id)
        );
    """)


    c.executemany(
        "INSERT INTO ligas (nosaukums, sezona) VALUES (?, ?)",
        [
            ("Vieriešu Virslīga",  "2025/2026"),
            ("Vīriešu 1. līga", "2025/2026"),
            ("Vīriešu 2. līga",   "2025/2026"),
        ]
    )

 
    c.executemany(
        "INSERT INTO komandas (nosaukums, liga_id) VALUES (?, ?)",
        [
            ("Ulbroka", 1), ("Rubene", 1), ("Ķekava", 1), 
            ("Talsi", 1), ("Cēsis", 1), ("Lielvārde", 1), ("Valmiera", 1),
            
            ("Jelgava", 2), ("Mežaparks", 2), ("Rīga", 2), 
            ("Kuldīga", 2), ("Bauska", 2), ("Saulkalne", 2),
            
            ("Valmiera VSS", 3), ("Ādaži", 3), ("Saldus", 3), 
            ("NND", 3), ("Imanta", 3)
        ]
    )

    c.executemany(
        """INSERT INTO speles
           (liga_id, majas_komanda_id, viesi_komanda_id, majas_varti, viesi_varti, datums)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (1, 1, 2, 5, 4, "15.02.2026"), (1, 3, 4, 8, 2, "15.02.2026"),
            (1, 5, 6, 3, 7, "22.02.2026"), (1, 7, 1, 4, 4, "22.02.2026"),
            
            (2, 8, 9, 10, 5, "16.02.2026"), (2, 10, 11, 4, 7, "16.02.2026"),
            (2, 12, 13, 6, 3, "23.02.2026"), (2, 9, 12, 2, 5, "23.02.2026"),
            
            (3, 14, 15, 6, 6, "17.02.2026"), (3, 16, 17, 1, 9, "17.02.2026"),
            (3, 18, 14, 12, 4, "24.02.2026"), (3, 15, 18, 3, 3, "24.02.2026"),
        ]
    )

    c.executemany(
        """INSERT INTO lietotaji (vards, lietotajvards, loma, parole_hash)
           VALUES (?, ?, ?, ?)""",
        [
            ("Administrators", "admin", "tiesnesis", generate_password_hash("Admin123!")),
            ("Kārlis", "karlis", "skatitajs", generate_password_hash("Parole123")),
            ("Anna Liepa", "anna_l", "skatitajs", generate_password_hash("Anna2026!")),
            ("Peteris Koks", "petis_k", "skatitajs", generate_password_hash("Petis789!")),
        ]
    )

    conn.commit()
    conn.close()

try:
    conn = get_db()
    conn.execute("SELECT 1 FROM ligas LIMIT 1")
    conn.close()
    print("Datubāze atrasta un ir darba kārtībā.")
except:
    print("Datubāze nav atrasta vai ir tukša. Veidojam no jauna...")
    izveidot_db()


@app.route("/")
def sakums():
  conn = get_db()
  ligas = conn.execute("SELECT * FROM ligas").fetchall()
  conn.close()
  return render_template("index.html", ligas=ligas)


@app.route("/tabula/<int:liga_id>")
def tabula(liga_id):
    conn = get_db()
    liga = conn.execute("SELECT * FROM ligas WHERE id = ?", (liga_id,)).fetchone()
 
    if not liga:
        conn.close()
        flash("Šāda līga neeksistē!", "error")
        return redirect(url_for("sakums"))
 
    komandas_raw = conn.execute(
        "SELECT * FROM komandas WHERE liga_id = ?", (liga_id,)
    ).fetchall()
    speles = conn.execute(
        "SELECT * FROM speles WHERE liga_id = ?", (liga_id,)
    ).fetchall()
    conn.close()
 
  
    stat = {}
    for k in komandas_raw:
        stat[k["id"]] = {
            "id": k["id"], "nosaukums": k["nosaukums"],
            "speles": 0, "uzvaras": 0, "zaudejumi": 0,
            "neizskirts": 0, "guti": 0, "ielaistie": 0, "punkti": 0
        }
 
    for s in speles:
        majas  = s["majas_komanda_id"]
        viesi  = s["viesi_komanda_id"]
        majas_goli = s["majas_varti"]
        viesi_goli = s["viesi_varti"]
 
        if majas in stat and viesi in stat:
            stat[majas]["speles"] += 1
            stat[viesi]["speles"] += 1
            stat[majas]["guti"]      += majas_goli
            stat[majas]["ielaistie"] += viesi_goli
            stat[viesi]["guti"]      += viesi_goli
            stat[viesi]["ielaistie"] += majas_goli
 
            if majas_goli > viesi_goli:
                stat[majas]["uzvaras"]  += 1
                stat[majas]["punkti"]   += 3
                stat[viesi]["zaudejumi"] += 1
            elif viesi_goli > majas_goli:
                stat[viesi]["uzvaras"]  += 1
                stat[viesi]["punkti"]   += 3
                stat[majas]["zaudejumi"] += 1
            else:
                stat[majas]["neizskirts"] += 1
                stat[viesi]["neizskirts"] += 1
                stat[majas]["punkti"] += 1
                stat[viesi]["punkti"] += 1
 
    top_komandas = sorted(stat.values(), key=lambda x: x["punkti"], reverse=True)
    return render_template("ligas.html", liga=liga, komandas=top_komandas)

@app.route("/speles/<int:liga_id>")
def speles(liga_id):
    conn = get_db()
    speles_saraksts = conn.execute("""
        SELECT s.id, s.datums, s.majas_varti, s.viesi_varti,
               m.nosaukums AS majas_vards, 
               v.nosaukums AS viesi_vards  
        FROM speles s
        JOIN komandas m ON s.majas_komanda_id = m.id
        JOIN komandas v ON s.viesi_komanda_id = v.id
        WHERE s.liga_id = ?
        ORDER BY s.datums DESC
    """, (liga_id,)).fetchall()
    conn.close()
    return render_template("speles.html", speles=speles_saraksts)

@app.route("/pieteikties", methods=["GET", "POST"])
def pieteikties():
    if request.method == "POST":
        lietotajs = request.form.get("lietotajs", "").strip()
        parole    = request.form.get("parole", "")
        conn = get_db()
        atbilde = conn.execute(
            "SELECT * FROM lietotaji WHERE lietotajvards = ?", (lietotajs,)
        ).fetchone()
        conn.close()
 
        if atbilde and check_password_hash(atbilde["parole_hash"], parole):
            session["id"] = atbilde["id"]
            session["vards"] = atbilde["vards"]
            session["lietotajs"] = atbilde["lietotajvards"]
            session["loma"] = atbilde["loma"]
            session["liga_id"] = atbilde["liga_id"]
            flash(f"Laipni lūgts, {atbilde['vards']}!", "success")
            return redirect(url_for("sakums"))
        else:
            flash("Nepareizs lietotājvārds vai parole!", "error")
            return render_template("pieteikties.html")
 
    return render_template("pieteikties.html")


@app.route("/registreties", methods=["GET", "POST"])
def registreties():
    conn = get_db()
    if request.method == "POST":
        vards = request.form.get("vards", "")
        lietotajvards = request.form.get("lietotajs", "")
        parole_txt = request.form.get("parole", "")
        parole = generate_password_hash(parole_txt)
        liga_id = request.form.get("liga_id")
        try:
            conn.execute(
                "INSERT INTO lietotaji (vards, lietotajvards, loma, parole_hash, liga_id) VALUES (?, ?, ?, ?, ?)",
                (vards, lietotajvards, "skatitajs", parole, liga_id)
            )
            conn.commit()
            flash("Reģistrācija veiksmīga!", "success")
            return redirect(url_for("pieteikties"))
        except sqlite3.IntegrityError:
            flash("Lietotājvārds jau ir aizņemts!", "error")
        finally:
            conn.close()
    ligas = conn.execute("SELECT * FROM ligas").fetchall()
    conn.close()
    return render_template("registreties.html", ligas=ligas)
 
@app.route("/atslegties")
def atslegties():
    session.clear()
    flash("Veiksmīgi izrakstījies!", "success")
    return redirect(url_for("sakums"))

@app.route("/piev_speli", methods=["GET", "POST"])
def piev_speli():
    if session.get("loma") != "tiesnesis":
        flash("Šī lapa ir pieejama tikai tiesnesim!", "error")
        return redirect(url_for("sakums"))
 
    conn = get_db()
 
    if request.method == "POST":
        liga_id  = request.form.get("liga_id", "")
        majas_id = request.form.get("majas_id", "")
        viesi_id = request.form.get("viesi_id", "")
        majas_v  = request.form.get("majas_varti", "")
        viesi_v  = request.form.get("viesi_varti", "")
        datums   = request.form.get("datums", "")
 
        if not liga_id or not majas_id or not viesi_id or not datums:
            flash("Nepareizi ievadīti dati!", "error")
        elif majas_id == viesi_id:
            flash("Mājas un viesi komanda nevar būt vienāda!", "error")
        elif not majas_v.isdigit() or not viesi_v.isdigit():
            flash("Nepareizi ievadīti dati!", "error")
        else:
            conn.execute("""
                INSERT INTO speles
                (liga_id, majas_komanda_id, viesi_komanda_id, majas_varti, viesi_varti, datums)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (liga_id, majas_id, viesi_id, int(majas_v), int(viesi_v), datums))
            conn.commit()
            conn.close()
            flash("Paldies par ievadītajiem datiem, veiksmi tālākos darbos.", "success")
            return redirect(url_for("speles"))
 
    ligas    = conn.execute("SELECT * FROM ligas").fetchall()
    komandas = conn.execute("SELECT * FROM komandas").fetchall()
    conn.close()
    return render_template("pievienot.html", ligas=ligas, komandas=komandas)

@app.route("/dz_speli/<int:spele_id>", methods=["GET", "POST"])
def dz_speli(spele_id):
    if session.get("loma") != "tiesnesis":
        flash("Šī lapa ir pieejama tikai tiesnesim!", "error")
        return redirect(url_for("sakums"))
 
    conn = get_db()
    spele = conn.execute("""
        SELECT s.id, s.majas_varti, s.viesi_varti, s.datums,
               m.nosaukums AS majas,
               v.nosaukums AS viesi
        FROM speles s
        JOIN komandas m ON s.majas_komanda_id = m.id
        JOIN komandas v ON s.viesi_komanda_id = v.id
        WHERE s.id = ?
    """, (spele_id,)).fetchone()
 
    if not spele:
        conn.close()
        flash("Šāda spēle neeksistē!", "error")
        return redirect(url_for("speles"))
 
    if request.method == "POST":
        conn.execute("DELETE FROM speles WHERE id = ?", (spele_id,))
        conn.commit()
        conn.close()
        flash("Spēle veiksmīgi dzēsta.", "success")
        return redirect(url_for("speles"))
 
    conn.close()
    return render_template("dzest.html", spele=spele)

@app.route("/lab_speli/<int:spele_id>", methods=["GET", "POST"])
def lab_speli(spele_id):
    if session.get("loma") != "tiesnesis":
        flash("Šī lapa ir pieejama tikai tiesnesim!", "error")
        return redirect(url_for("sakums"))
 
    conn = get_db()
 
    if request.method == "POST":
        majas_v = request.form.get("majas_varti", "")
        viesi_v = request.form.get("viesi_varti", "")
        datums  = request.form.get("datums", "")
 
        if not majas_v.isdigit() or not viesi_v.isdigit() or not datums:
            flash("Nepareizi ievadīti dati!", "error")
        else:
            conn.execute("""
                UPDATE speles
                SET majas_varti = ?, viesi_varti = ?, datums = ?
                WHERE id = ?
            """, (int(majas_v), int(viesi_v), datums, spele_id))
            conn.commit()
            conn.close()
            flash("Paldies par ievadītajiem datiem, veiksmi tālākos darbos.", "success")
            return redirect(url_for("speles"))
 
    spele = conn.execute("""
        SELECT s.id, s.majas_varti, s.viesi_varti, s.datums,
               m.nosaukums AS majas,
               v.nosaukums AS viesi
        FROM speles s
        JOIN komandas m ON s.majas_komanda_id = m.id
        JOIN komandas v ON s.viesi_komanda_id = v.id
        WHERE s.id = ?
    """, (spele_id,)).fetchone()
    conn.close()
 
    if not spele:
        flash("Šāda spēle neeksistē!", "error")
        return redirect(url_for("speles"))
 
    return render_template("labot.html", spele=spele)
 
if __name__ == '__main__':
    app.run(debug=True)