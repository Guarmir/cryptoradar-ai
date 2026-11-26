-- Internal challenges; no plaintext proof or FCM token stored.
CREATE TABLE IF NOT EXISTS cryptoradar_fcm_possession_challenges (
    scope_key TEXT NOT NULL,
    challenge_id TEXT NOT NULL,
    firebase_auth_uid TEXT NOT NULL,
    destination_hash TEXT NOT NULL,
    proof_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (scope_key, challenge_id)
);
CREATE INDEX IF NOT EXISTS idx_cr_fcm_challenge_expiry
    ON cryptoradar_fcm_possession_challenges (expires_at);
