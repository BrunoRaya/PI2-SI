from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .db import get_db


bp = Blueprint("main", __name__)
MANCHESTER = {
    "vermelho": (1, "Emergencia - atendimento imediato"),
    "laranja": (2, "Muito urgente"),
    "amarelo": (3, "Urgente"),
    "verde": (4, "Pouco urgente"),
    "azul": (5, "Nao urgente"),
}


def attendance_or_404(attendance_id):
    attendance = get_db().execute(
        """
        SELECT a.*, p.full_name, p.cpf, p.rg, p.birth_date, p.father_name,
               p.mother_name, p.address, p.phone,
               t.blood_pressure, t.temperature, t.heart_rate, t.complaints, t.manchester
        FROM attendances a
        JOIN patients p ON p.id = a.patient_id
        LEFT JOIN triages t ON t.attendance_id = a.id
        WHERE a.id = ?
        """,
        (attendance_id,),
    ).fetchone()
    if attendance is None:
        abort(404)
    return attendance


def ensure_editable(attendance):
    if attendance["status"] in {"finalizado", "cancelado"} or attendance["confirmed_at"]:
        abort(409, "Este atendimento nao pode mais ser alterado.")


@bp.get("/")
def index():
    database = get_db()
    counts = {
        row["status"]: row["total"]
        for row in database.execute(
            "SELECT status, COUNT(*) AS total FROM attendances GROUP BY status"
        ).fetchall()
    }
    recent = database.execute(
        """
        SELECT a.id, a.code, a.status, a.created_at, p.full_name
        FROM attendances a JOIN patients p ON p.id = a.patient_id
        ORDER BY a.id DESC LIMIT 8
        """
    ).fetchall()
    return render_template("index.html", counts=counts, recent=recent)


@bp.get("/recepcao")
def reception():
    query = request.args.get("q", "").strip()
    sql = """
        SELECT a.id, a.code, a.status, a.created_at, p.full_name, p.cpf
        FROM attendances a JOIN patients p ON p.id = a.patient_id
    """
    params = ()
    if query:
        sql += " WHERE a.code LIKE ? OR p.full_name LIKE ? OR p.cpf LIKE ?"
        term = f"%{query}%"
        params = (term, term, term)
    sql += " ORDER BY a.id DESC"
    attendances = get_db().execute(sql, params).fetchall()
    return render_template("reception/list.html", attendances=attendances, query=query)


@bp.route("/recepcao/novo", methods=("GET", "POST"))
def create_attendance():
    if request.method == "POST":
        required = ("full_name", "cpf", "birth_date", "address")
        missing = [field for field in required if not request.form.get(field, "").strip()]
        if missing:
            flash("Preencha nome, CPF, data de nascimento e endereco.", "error")
            return render_template("reception/form.html", attendance=None)

        database = get_db()
        cpf = request.form["cpf"].strip()
        patient = database.execute("SELECT id FROM patients WHERE cpf = ?", (cpf,)).fetchone()
        patient_values = (
            request.form["full_name"].strip(),
            request.form.get("rg", "").strip(),
            request.form["birth_date"],
            request.form.get("father_name", "").strip(),
            request.form.get("mother_name", "").strip(),
            request.form["address"].strip(),
            request.form.get("phone", "").strip(),
        )
        if patient:
            patient_id = patient["id"]
            database.execute(
                """UPDATE patients SET full_name=?, rg=?, birth_date=?, father_name=?,
                   mother_name=?, address=?, phone=? WHERE id=?""",
                (*patient_values, patient_id),
            )
        else:
            cursor = database.execute(
                """INSERT INTO patients
                   (full_name, rg, birth_date, father_name, mother_name, address, phone, cpf)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (*patient_values, cpf),
            )
            patient_id = cursor.lastrowid

        cursor = database.execute(
            "INSERT INTO attendances (patient_id) VALUES (?)", (patient_id,)
        )
        attendance_id = cursor.lastrowid
        code = f"AT{attendance_id:04d}"
        database.execute("UPDATE attendances SET code = ? WHERE id = ?", (code, attendance_id))
        database.commit()
        flash(f"Atendimento {code} criado com sucesso.", "success")
        return redirect(url_for("main.attendance_detail", attendance_id=attendance_id))

    return render_template("reception/form.html", attendance=None)


@bp.get("/atendimentos/<int:attendance_id>")
def attendance_detail(attendance_id):
    attendance = attendance_or_404(attendance_id)
    medications = get_db().execute(
        "SELECT * FROM medications WHERE attendance_id = ? ORDER BY id", (attendance_id,)
    ).fetchall()
    return render_template(
        "attendance_detail.html", attendance=attendance, medications=medications
    )


@bp.route("/recepcao/<int:attendance_id>/editar", methods=("GET", "POST"))
def edit_attendance(attendance_id):
    attendance = attendance_or_404(attendance_id)
    ensure_editable(attendance)
    if request.method == "POST":
        required = ("full_name", "birth_date", "address")
        if any(not request.form.get(field, "").strip() for field in required):
            flash("Preencha nome, data de nascimento e endereco.", "error")
        else:
            database = get_db()
            database.execute(
                """
                UPDATE patients SET full_name=?, rg=?, birth_date=?, father_name=?,
                    mother_name=?, address=?, phone=? WHERE id=?
                """,
                (
                    request.form["full_name"].strip(),
                    request.form.get("rg", "").strip(),
                    request.form["birth_date"],
                    request.form.get("father_name", "").strip(),
                    request.form.get("mother_name", "").strip(),
                    request.form["address"].strip(),
                    request.form.get("phone", "").strip(),
                    attendance["patient_id"],
                ),
            )
            database.commit()
            flash("Dados atualizados.", "success")
            return redirect(url_for("main.attendance_detail", attendance_id=attendance_id))
    return render_template("reception/form.html", attendance=attendance)


@bp.post("/recepcao/<int:attendance_id>/cancelar")
def cancel_attendance(attendance_id):
    attendance = attendance_or_404(attendance_id)
    ensure_editable(attendance)
    database = get_db()
    database.execute(
        "UPDATE attendances SET status='cancelado', canceled_at=CURRENT_TIMESTAMP WHERE id=?",
        (attendance_id,),
    )
    database.commit()
    flash(f"Atendimento {attendance['code']} cancelado.", "success")
    return redirect(url_for("main.reception"))


@bp.get("/triagem")
def triage_queue():
    attendances = get_db().execute(
        """
        SELECT a.id, a.code, a.status, a.created_at, p.full_name
        FROM attendances a JOIN patients p ON p.id = a.patient_id
        WHERE a.status IN ('aguardando_triagem', 'aguardando_medico')
        ORDER BY CASE a.status WHEN 'aguardando_triagem' THEN 0 ELSE 1 END, a.created_at
        """
    ).fetchall()
    return render_template("triage/list.html", attendances=attendances)


@bp.route("/triagem/<int:attendance_id>", methods=("GET", "POST"))
def triage(attendance_id):
    attendance = attendance_or_404(attendance_id)
    ensure_editable(attendance)
    if request.method == "POST":
        required = ("blood_pressure", "temperature", "heart_rate", "complaints", "manchester")
        if any(not request.form.get(field, "").strip() for field in required):
            flash("Preencha todos os dados da triagem.", "error")
        elif request.form["manchester"] not in MANCHESTER:
            abort(400)
        else:
            try:
                temperature = float(request.form["temperature"].replace(",", "."))
                heart_rate = int(request.form["heart_rate"])
            except ValueError:
                flash("Temperatura e batimentos devem ser numeros validos.", "error")
            else:
                database = get_db()
                database.execute(
                    """
                    INSERT INTO triages
                        (attendance_id, blood_pressure, temperature, heart_rate, complaints, manchester)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(attendance_id) DO UPDATE SET
                        blood_pressure=excluded.blood_pressure,
                        temperature=excluded.temperature,
                        heart_rate=excluded.heart_rate,
                        complaints=excluded.complaints,
                        manchester=excluded.manchester,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        attendance_id,
                        request.form["blood_pressure"].strip(),
                        temperature,
                        heart_rate,
                        request.form["complaints"].strip(),
                        request.form["manchester"],
                    ),
                )
                database.execute(
                    "UPDATE attendances SET status='aguardando_medico' WHERE id=?",
                    (attendance_id,),
                )
                database.commit()
                flash("Triagem registrada e enviada ao painel medico.", "success")
                return redirect(url_for("main.triage_queue"))
    return render_template(
        "triage/form.html", attendance=attendance, manchester=MANCHESTER
    )


@bp.get("/medico")
def doctor_panel():
    attendances = get_db().execute(
        """
        SELECT a.id, a.code, a.status, a.created_at, p.full_name, p.birth_date,
               t.manchester, t.complaints
        FROM attendances a
        JOIN patients p ON p.id = a.patient_id
        JOIN triages t ON t.attendance_id = a.id
        WHERE a.status IN ('aguardando_medico', 'em_atendimento')
        ORDER BY CASE t.manchester
            WHEN 'vermelho' THEN 1 WHEN 'laranja' THEN 2 WHEN 'amarelo' THEN 3
            WHEN 'verde' THEN 4 ELSE 5 END, a.created_at
        """
    ).fetchall()
    return render_template("doctor/panel.html", attendances=attendances)


@bp.route("/medico/<int:attendance_id>", methods=("GET", "POST"))
def doctor_attendance(attendance_id):
    attendance = attendance_or_404(attendance_id)
    if attendance["status"] not in {"aguardando_medico", "em_atendimento"}:
        abort(409, "O atendimento nao esta disponivel no painel medico.")
    database = get_db()
    if attendance["status"] == "aguardando_medico":
        database.execute(
            "UPDATE attendances SET status='em_atendimento' WHERE id=?", (attendance_id,)
        )
        database.commit()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "medication":
            name = request.form.get("name", "").strip()
            dosage = request.form.get("dosage", "").strip()
            if not name or not dosage:
                flash("Informe o medicamento e a dosagem.", "error")
            else:
                database.execute(
                    "INSERT INTO medications (attendance_id, name, dosage, instructions) VALUES (?, ?, ?, ?)",
                    (attendance_id, name, dosage, request.form.get("instructions", "").strip()),
                )
                database.commit()
                flash("Medicacao registrada.", "success")
            return redirect(url_for("main.doctor_attendance", attendance_id=attendance_id))

        if action == "finish":
            notes = request.form.get("medical_notes", "").strip()
            if not notes:
                flash("Registre a avaliacao medica antes de finalizar.", "error")
            else:
                database.execute(
                    """UPDATE attendances SET status='finalizado', medical_notes=?,
                       confirmed_at=CURRENT_TIMESTAMP, discharged_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (notes, attendance_id),
                )
                database.commit()
                flash(f"Atendimento {attendance['code']} confirmado e finalizado.", "success")
                return redirect(url_for("main.doctor_panel"))

    medications = database.execute(
        "SELECT * FROM medications WHERE attendance_id=? ORDER BY id", (attendance_id,)
    ).fetchall()
    return render_template(
        "doctor/attendance.html", attendance=attendance, medications=medications
    )
