"""Registration-only store. Never overwrite an owned installation.

The authenticated enrollment creates device and owner in one transaction.
The legacy path waits for a conflicting insert, locks the existing device,
then checks ownership in a fresh READ COMMITTED statement.
Do not use this adapter for internal delivery or authenticated rotation.
"""
from app.push.postgresql_push_device_store import PostgreSQLPushDeviceStore
from app.push.push_device_registration_service import ProtectedInstallationRegistrationError


class PostgreSQLLegacyRegistrationStore(PostgreSQLPushDeviceStore):
    def save_device(self, device):
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
                values = (self.scope_key, device.installation_id, device.fcm_token,
                          device.firebase_installation_id, device.platform, device.enabled)
                cursor.execute('''INSERT INTO cryptoradar_push_devices
                    (scope_key, installation_id, fcm_token, firebase_installation_id,
                     platform, enabled, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (scope_key, installation_id) DO NOTHING
                    RETURNING installation_id''', values)
                if cursor.fetchone() is None:
                    key = values[:2]
                    cursor.execute('''SELECT installation_id FROM cryptoradar_push_devices
                        WHERE scope_key = %s AND installation_id = %s FOR UPDATE''', key)
                    if cursor.fetchone() is None:
                        raise ProtectedInstallationRegistrationError('Cadastro concorrente; tente novamente.')
                    cursor.execute('''SELECT firebase_auth_uid FROM cryptoradar_push_installation_owners
                        WHERE scope_key = %s AND installation_id = %s''', key)
                    if cursor.fetchone() is not None:
                        raise ProtectedInstallationRegistrationError('Instalacao protegida.')
                    cursor.execute('''UPDATE cryptoradar_push_devices SET
                        fcm_token = %s, firebase_installation_id = %s,
                        platform = %s, enabled = %s, updated_at = NOW()
                        WHERE scope_key = %s AND installation_id = %s''', values[2:] + key)
                    if cursor.rowcount != 1:
                        raise ProtectedInstallationRegistrationError('Cadastro concorrente; tente novamente.')
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()
