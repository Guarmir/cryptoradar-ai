-- Vinculos de autorizacao: NAO criar registros automaticamente por installation_id.
-- A vinculacao inicial requer comprovacao de posse por um fluxo confiavel,
-- a ser implementado antes da liberacao da API de preferencias.
CREATE TABLE IF NOT EXISTS cryptoradar_push_installation_owners (
    scope_key TEXT NOT NULL,
    installation_id TEXT NOT NULL,
    firebase_auth_uid TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (scope_key, installation_id),
    CONSTRAINT fk_cryptoradar_push_installation_owners_device
        FOREIGN KEY (scope_key, installation_id)
        REFERENCES cryptoradar_push_devices (scope_key, installation_id)
        ON DELETE CASCADE,
    CONSTRAINT ck_cryptoradar_push_installation_owners_uid
        CHECK (LENGTH(BTRIM(firebase_auth_uid)) > 0)
);
CREATE INDEX IF NOT EXISTS idx_cryptoradar_push_installation_owners_uid
    ON cryptoradar_push_installation_owners (scope_key, firebase_auth_uid);
