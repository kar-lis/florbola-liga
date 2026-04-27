from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "florbols67"

fails = "florbols.db"

def get_db():
    conn = sqlite3.connect(fails)
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
            parole_hash   TEXT NOT NULL
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
            ("Ulbroka",  1),
            ("Rubene",       1),
            ("Ķekava",       1),
            ("Tasi",         1),
            ("Cesis",        1),
            ("Jelgava",      2),
            ("Mezaparks",    2),
            ("Riga",    2),
            ("Valmiera",     3),
            ("Adazi",        3),
        ]
    )

    c.executemany(
        """INSERT INTO speles
           (liga_id, majas_komanda_id, viesi_komanda_id, majas_varti, viesi_varti, datums)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (1, 1, 2,  7,  3, "07.02.2026"),
            (1, 3, 4,  5,  2, "07.02.2026"),
            (1, 5, 6,  4,  4, "08.02.2026"),
            (1, 2, 3,  6,  5, "14.02.2026"),
            (1, 4, 5,  3,  8, "14.02.2026"),
            (1, 1, 3,  9,  4, "21.02.2026"),
            (1, 6, 2,  2,  7, "21.02.2026"),
            (1, 5, 1,  3, 10, "28.02.2026"),
            (1, 4, 6,  6,  1, "28.02.2026"),
            (1, 3, 5,  5,  6, "07.03.2026"),
        ]
    )

    c.executemany(
        """INSERT INTO lietotaji (vards, lietotajvards, loma, parole_hash)
           VALUES (?, ?, ?, ?)""",
        [
            ("Administrators", "admin",      "tiesnesis", generate_password_hash("Admin123!")),
            ("Tiesnesis1",     "tiesnesis1", "tiesnesis", generate_password_hash("Parole456!")),
            ("Janis Skatitajs","janis_s",    "skatitajs", generate_password_hash("Skatitajs1!")),
            ("Anna Liepa",     "anna_l",     "skatitajs", generate_password_hash("Anna2026!")),
            ("Peteris Koks",   "petis_k",    "skatitajs", generate_password_hash("Petis789!")),
        ]
    )

    conn.commit()
    conn.close()

try:
    conn = get_db()
    conn.execute("SELECT 1 FROM ligas LIMIT 1")
    conn.close()
except:
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
            "neizskirti": 0, "guti": 0, "ielaistie": 0, "punkti": 0
        }
 
    for s in speles:
        majas  = s["majas_komanda_id"]
        viesi  = s["viesi_komanda_id"]
        majas_goli = s["majas_varti"]
        viesi_goli = s["viesi_varti"]
 
        if majas in stat and viesi in stat:
            stat[majas]["speles"] += 1
            stat[viesi]["speles"] += 1
            stat[majas]["guti"]      += mg
            stat[majas]["ielaistie"] += vg
            stat[viesi]["guti"]      += vg
            stat[viesi]["ielaistie"] += mg
 
            if majas_goli > viesi_goli:
                stat[majas]["uzvaras"]  += 1
                stat[majas]["punkti"]   += 3
                stat[viesi]["zaudejumi"] += 1
            elif vg > mg:
                stat[viesi]["uzvaras"]  += 1
                stat[viesi]["punkti"]   += 3
                stat[majas]["zaudejumi"] += 1
            else:
                stat[majas]["neizskirts"] += 1
                stat[viesi]["neizskirts"] += 1
                stat[majas]["punkti"] += 1
                stat[viesi]["punkti"] += 1
 
    komandas = sorted(stat.values(), key=lambda x: x["punkti"], reverse=True)
    return render_template("ligas.html", liga=liga, komandas=komandas)

@app.route("/speles")
def speles():
    conn = get_db()
    speles_saraksts = conn.execute("""
        SELECT s.id, s.majas_varti, s.viesi_varti, s.datums,
               m.nosaukums AS majas,
               v.nosaukums AS viesi
        FROM speles s
        JOIN komandas m ON s.majas_komanda_id = m.id
        JOIN komandas v ON s.viesi_komanda_id = v.id
        ORDER BY s.datums DESC
    """).fetchall()
    conn.close()
    return render_template("speles.html", speles=speles_saraksts)

@app.route("/pieteikties", methods=["GET", "POST"])
def pieteikties():
    if request.method == "POST":
        lietotajs = request.form.get("lietotajs", "").strip()
        parole    = request.form.get("parole", "")
 
        if not lietotajs or not parole:
            flash("Nepareizi ievadīti dati!", "error")
            return render_template("pieteikties.html")
 
        conn = get_db()
        atbilde = conn.execute(
            "SELECT * FROM lietotaji WHERE lietotajvards = ?", (lietotajs,)
        ).fetchone()
        conn.close()
 
        if atbilde and check_password_hash(atbilde["parole_hash"], parole):
            session["id"]        = atbilde["id"]
            session["vards"]     = atbilde["vards"]
            session["lietotajs"] = atbilde["lietotajvards"]
            session["loma"]      = atbilde["loma"]
            flash(f"Laipni lūgts, {atbilde['vards']}!", "success")
            return redirect(url_for("sakums"))
        else:
            flash("Nepareizi ievadīti dati!", "error")
 
    return render_template("pieteikties.html")


@app.route("/registreties", methods=["GET", "POST"])
def registreties():
    if request.method == "POST":
        vards         = request.form.get("vards", "").strip()
        lietotajvards = request.form.get("lietotajs", "").strip()
        parole_txt    = request.form.get("parole", "")
        loma          = request.form.get("loma", "skatitajs")
 
        if not vards or not lietotajvards or not parole_txt:
            flash("Nepareizi ievadīti dati!", "error")
            return render_template("registreties.html")
 
        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO lietotaji (vards, lietotajvards, loma, parole_hash) VALUES (?, ?, ?, ?)",
                (vards, lietotajvards, loma, generate_password_hash(parole_txt))
            )
            conn.commit()
            conn.close()
            flash("Profils izveidots! Vari pieteikties.", "success")
            return redirect(url_for("pieteikties"))
        except sqlite3.IntegrityError:
            flash("Šāds lietotājvārds jau eksistē!", "error")
 
    return render_template("registreties.html")
 
 
@app.route("/atslegties")
def atslegties():
    session.clear()
    flash("Veiksmīgi izrakstījies!", "success")
    return redirect(url_for("sakums"))

if __name__ == '__main__':
    app.run(debug=True)