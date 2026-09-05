CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    rg TEXT,
    birth_date TEXT NOT NULL,
    father_name TEXT,
    mother_name TEXT,
    address TEXT NOT NULL,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    patient_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'aguardando_triagem'
        CHECK (status IN ('aguardando_triagem', 'aguardando_medico', 'em_atendimento', 'finalizado', 'cancelado')),
    medical_notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    canceled_at TEXT,
    confirmed_at TEXT,
    discharged_at TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE TABLE IF NOT EXISTS triages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attendance_id INTEGER NOT NULL UNIQUE,
    blood_pressure TEXT NOT NULL,
    temperature REAL NOT NULL,
    heart_rate INTEGER NOT NULL,
    complaints TEXT NOT NULL,
    manchester TEXT NOT NULL
        CHECK (manchester IN ('vermelho', 'laranja', 'amarelo', 'verde', 'azul')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attendance_id) REFERENCES attendances(id)
);

CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attendance_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    instructions TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attendance_id) REFERENCES attendances(id)
);

CREATE INDEX IF NOT EXISTS idx_attendances_status ON attendances(status);
CREATE INDEX IF NOT EXISTS idx_attendances_patient ON attendances(patient_id);
CREATE INDEX IF NOT EXISTS idx_triages_manchester ON triages(manchester);
