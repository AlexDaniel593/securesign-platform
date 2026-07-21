from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from app.core.config import settings

_private_key = None
_public_key = None
_ca_cert = None


def _get_or_create_ca_key():
    global _private_key, _public_key
    if _private_key is None:
        _private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        _public_key = _private_key.public_key()
    return _private_key, _public_key


def get_ca_certificate():
    global _ca_cert
    if _ca_cert is None:
        _ca_cert = _build_ca_cert()
    return _ca_cert


def _build_ca_cert():
    private_key, public_key = _get_or_create_ca_key()

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, settings.CA_COUNTRY),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, settings.CA_STATE),
        x509.NameAttribute(NameOID.LOCALITY_NAME, settings.CA_LOCALITY),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, settings.CA_ORG),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, settings.CA_ORG_UNIT),
        x509.NameAttribute(NameOID.COMMON_NAME, settings.CA_COMMON_NAME),
    ])

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=settings.CA_VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key, hashes.SHA256())
    )

    return cert


def issue_certificate(subject_name: str, public_key_pem: str, validity_days: int = 365) -> dict:
    private_key, ca_public_key = _get_or_create_ca_key()

    public_key = serialization.load_pem_public_key(public_key_pem.encode())

    now = datetime.now(timezone.utc)
    valid_from = now
    valid_to = now + timedelta(days=validity_days)

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, settings.CA_COUNTRY),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, settings.CA_ORG),
        x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
    ])

    issuer_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, settings.CA_COUNTRY),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, settings.CA_STATE),
        x509.NameAttribute(NameOID.LOCALITY_NAME, settings.CA_LOCALITY),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, settings.CA_ORG),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, settings.CA_ORG_UNIT),
        x509.NameAttribute(NameOID.COMMON_NAME, settings.CA_COMMON_NAME),
    ])

    serial_number = x509.random_serial_number()

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer_name)
        .public_key(public_key)
        .serial_number(serial_number)
        .not_valid_before(valid_from)
        .not_valid_after(valid_to)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(private_key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()

    fingerprint = cert.fingerprint(hashes.SHA256()).hex()

    return {
        "certificate_pem": cert_pem,
        "serial_number": str(serial_number),
        "subject": subject_name,
        "issuer": settings.CA_COMMON_NAME,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "fingerprint": fingerprint,
    }


def verify_certificate_pem(certificate_pem: str) -> dict:
    try:
        cert = x509.load_pem_x509_certificate(certificate_pem.encode())

        now = datetime.now(timezone.utc)

        if now < cert.not_valid_before_utc:
            return {"valid": False, "reason": "Certificate is not yet valid"}

        if now > cert.not_valid_after_utc:
            return {"valid": False, "reason": "Certificate has expired"}

        try:
            ca_cert_obj = get_ca_certificate()
            ca_pub_key = ca_cert_obj.public_key()
        except Exception:
            ca_pub_key = _get_or_create_ca_key()[1]

        try:
            ca_pub_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )
            signature_valid = True
        except Exception:
            signature_valid = False

        if not signature_valid:
            return {"valid": False, "reason": "Invalid certificate signature"}

        expires_in_days = (cert.not_valid_after_utc - now).days

        return {"valid": True, "reason": "Certificate is valid", "expires_in_days": expires_in_days}

    except Exception as e:
        return {"valid": False, "reason": f"Invalid certificate format: {str(e)}"}
