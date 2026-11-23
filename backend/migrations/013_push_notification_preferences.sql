-- Preferencias de notificacao por instalacao e escopo de push.
-- Registros antigos sem preferencias permanecem habilitados por padrao.
-- Esta migracao nao altera a tabela de cadastro nem o scanner.
CREATE TABLE IF NOT EXISTS cryptoradar_push_notification_preferences (
    scope_key TEXT NOT NULL,
    installation_id TEXT NOT NULL,
    observation_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    early_movement_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    confirmed_movement_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (scope_key, installation_id),
    CONSTRAINT fk_cryptoradar_push_notification_preferences_device
        FOREIGN KEY (scope_key, installation_id)
        REFERENCES cryptoradar_push_devices (scope_key, installation_id)
        ON DELETE CASCADE
);
