from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "florbols67"

fails = "florbols.db"


def izveidot_db():
    savienojums = sqlite3.connect(fails)
    savienojums.execute("PRAGMA foreign_keys = ON")
    kursors = savienojums.cursor()


    kursors.executescript("""
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


    kursors.executemany(
        "INSERT INTO ligas (nosaukums, sezona) VALUES (?, ?)",
        [
            ("Vieriešu Virslīga",  "2025/2026"),
            ("Vīriešu 1. līga", "2025/2026"),
            ("Vīriešu 2. līga",   "2025/2026"),
        ]
    )

 
    kursors.executemany(
        "INSERT INTO komandas (nosaukums, liga_id) VALUES (?, ?)",
        [
            ("Ulbroka/NAU",  1),
            ("Rubene",       1),
            ("Ķekava",       1),
            ("Tasi",         1),
            ("Cesis",        1),
            ("Jelgava",      2),
            ("Mezaparks",    2),
            ("Riga/LSPA",    2),
            ("Valmiera",     3),
            ("Adazi",        3),
        ]
    )

    kursors.executemany(
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

    kursors.executemany(
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
    savienojums.close()
    print("Datubaze izveidota un aizpildita!")
    print(f"  Fails: {fails}")



@app.route("/")
def sakums:
	return render_template("index.html")

@app.route("/pieteikties", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        lietotajs = request.form.get('lietotajs')
        parole = request.form.get('parole')

        conn = sqlite3.connect("florbols.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM lietotaji WHERE lietotajvards = ?", (lietotajs,))
        atbilde = c.fetchone()
        conn.close()

        if atbilde and check_password_hash(atbilde['parole'], parole):
            session["id"] = atbilde["id"]
            session["vards"] = atbilde["vards"]
            session["lietotajs"] = atbilde["lietotajvards"]
            session["loma"] = 'klients'
            return redirect("/")
        else:
            return "Nepareizi dati!"

    return render_template("pieteikties.html")

def registreties():
    if request.method == 'POST':
    	vards = request.form.get("vards")
        lietotajvards = request.form.get("lietotajs")
        parole_txt = request.form.get("parole")
        parole = generate_password_hash(parole_txt)
        conn = sqlite3.connect("florbols.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        insert_sql = """
                    INSERT INTO lietotaji (vards, lietotajvards, parole)
                    VALUES (?, ?, ?, ?)
                    """
        insert_dati = (lietotajvards, vards, parole)
        c.execute(insert_sql, insert_dati)
        conn.commit()
        return redirect("/pieteikties")

    return render_template("registreties.html")
    

@app.route('/atslegties')
def logout():
    session.clear() 
    return redirect(url_for('sakums'))

if __name__ == '__main__':
    app.run(debug=True)