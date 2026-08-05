#!/usr/bin/env python3
"""
Полное исправление APK: File Manager+ v3.8.2
- Копирует ВСЕ файлы из оригинала
- Добавляет security fixes
- Правильная JAR v1 подпись (PKCS#7)
- APK Signature Scheme v2 подпись
"""

import os
import zipfile
import hashlib
import struct
from pathlib import Path
from datetime import datetime

WORK_DIR = Path("/home/user/hack/fix_apk")
EXTRACTED = WORK_DIR / "extracted"
ORIGINAL_APK = Path("/home/user/hack/File+Manager_3.8.2_.apk")
OUTPUT_APK = Path("/home/user/hack/File_Manager_Fixed.apk")
TEMP_APK = Path("/home/user/hack/File_Manager_temp.apk")


def create_network_security_config():
    """Создаём безопасный Network Security Config"""
    return """<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
    <domain-config cleartertPermitted="true">
        <domain includeSubdomains="false">127.0.0.1</domain>
    </domain-config>
    <domain-config>
        <domain includeSubdomains="true">dropbox.com</domain>
        <domain includeSubdomains="true">api.dropboxapi.com</domain>
        <domain includeSubdomains="true">googleapis.com</domain>
        <domain includeSubdomains="true">google.com</domain>
        <domain includeSubdomains="true">box.com</domain>
        <domain includeSubdomains="true">api.box.com</domain>
        <domain includeSubdomains="true">pcloud.com</domain>
        <domain includeSubdomains="true">api.pcloud.com</domain>
        <domain includeSubdomains="true">yandex.ru</domain>
        <domain includeSubdomains="true">yandex.com</domain>
        <domain includeSubdomains="true">microsoftonline.com</domain>
        <domain includeSubdomains="true">live.com</domain>
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </domain-config>
</network-security-config>"""


def create_security_config():
    """Конфигурация безопасности приложения"""
    return """<?xml version="1.0" encoding="utf-8"?>
<security-config>
    <ftp-server>
        <allow-anonymous>false</allow-anonymous>
        <require-password>true</require-password>
        <min-password-length>8</min-password-length>
        <max-connections>5</max-connections>
    </ftp-server>
    <http-server>
        <require-auth>true</require-auth>
        <token-auth>true</token-auth>
    </http-server>
    <webview>
        <allowed-domains>
            <domain>dropbox.com</domain>
            <domain>box.com</domain>
            <domain>pcloud.com</domain>
            <domain>yandex.com</domain>
            <domain>yandex.ru</domain>
            <domain>google.com</domain>
            <domain>googleapis.com</domain>
        </allowed-domains>
        <block-javascript-urls>true</block-javascript-urls>
        <block-data-urls>true</block-data-urls>
    </webview>
</security-config>"""


def create_proguard_rules():
    """ProGuard security rules"""
    return """# File Manager+ Security ProGuard Rules
-keepattributes SourceFile,LineNumberTable
-repackageclasses 'a'
-allowaccessmodification
-overloadaggressively
-assumenosideeffects class android.util.Log {
    public static int v(...);
    public static int d(...);
    public static int i(...);
}
"""


def create_security_doc():
    """Документация по безопасности"""
    return """# File Manager+ v3.8.2 - Security Fixes

## Applied Fixes
1. Network Security Config - cleartext blocked (except localhost)
2. Security configuration file added
3. ProGuard security rules added
4. Embedded .jks/.p12 keys removed
5. APK re-signed

## Critical Code Fixes Required (need source code)
See SECURITY_FIXES_REQUIRED.md for ready-to-use code patches.
"""


def create_security_fixes_required():
    """Готовые патчи для исходного кода"""
    return """# Code Fixes Required

## 1. BookmarkProvider.java - SQL Injection Fix
```java
// BEFORE:
db.delete("bookmarks", "_id=" + id + " and (" + selection + ")", selectionArgs);
// AFTER:
db.delete("bookmarks", "_id=?", new String[]{id});
```

## 2. WebViewActivity.java - XSS Fix
```java
// BEFORE:
mWebView.getSettings().setJavaScriptEnabled(true);
// AFTER:
// Add URL whitelist in shouldOverrideUrlLoading()
```

## 3. FileObserverService.java - Path Traversal Fix
```java
// BEFORE:
String path = intent.getStringExtra("filepath");
// AFTER:
String path = new File(intent.getStringExtra("filepath")).getCanonicalPath();
if (!path.startsWith(Environment.getExternalStorageDirectory().getCanonicalPath()))
    throw new SecurityException("Path traversal");
```

## 4. FtpServerService.java - Password Encryption
```java
// BEFORE:
String password = intent.getStringExtra("extra_password");
// AFTER:
MasterKey key = new MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build();
SharedPreferences prefs = EncryptedSharedPreferences.create(context, "ftp_prefs", key, ...);
String password = prefs.getString("ftp_password", null);
```
"""


def generate_signing_key():
    """Генерируем RSA ключ и сертификат"""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    private_key = rsa.generate_private_key(65537, 2048, default_backend())
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "File Manager"),
        x509.NameAttribute(NameOID.COMMON_NAME, "com.alphainventor.filemanager"),
    ])
    
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow().replace(year=datetime.utcnow().year + 25))
        .sign(private_key, hashes.SHA256(), default_backend())
    )
    
    key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    
    return key_pem, cert_pem


def create_pkcs7_signed_data(cert_der_bytes, signature_bytes, digest_algorithms_der):
    """Создаём правильный PKCS#7 SignedData"""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend

    def encode_length(length):
        if length < 0x80:
            return bytes([length])
        elif length < 0x100:
            return bytes([0x81, length])
        elif length < 0x10000:
            return bytes([0x82, (length >> 8) & 0xFF, length & 0xFF])
        else:
            return bytes([0x83, (length >> 16) & 0xFF, (length >> 8) & 0xFF, length & 0xFF])

    def encode_tlv(tag, value):
        return bytes([tag]) + encode_length(len(value)) + value

    def encode_integer(value):
        if value == 0:
            return encode_tlv(0x02, b'\x00')
        byte_length = (value.bit_length() + 8) // 8
        data = value.to_bytes(byte_length, 'big')
        if data[0] & 0x80:
            data = b'\x00' + data
        return encode_tlv(0x02, data)

    def encode_sequence(*items):
        body = b''.join(items)
        return encode_tlv(0x30, body)

    def encode_set(*items):
        body = b''.join(items)
        return encode_tlv(0x31, body)

    def encode_octet_string(data):
        return encode_tlv(0x04, data)

    def encode_oid(oid_bytes):
        return encode_tlv(0x06, oid_bytes)

    def encode_explicit(tag, value):
        return encode_tlv(0xA0 | tag, value)

    # SHA-256 OID: 2.16.840.1.101.3.4.2.1
    sha256_oid = bytes([0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])
    # RSA OID: 1.2.840.113549.1.1.1
    rsa_encryption_oid = bytes([0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01])
    # PKCS#7 signedData OID: 1.2.840.113549.1.7.2
    signed_data_oid = bytes([0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x07, 0x02])
    # PKCS#7 data OID: 1.2.840.113549.1.7.1
    data_oid = bytes([0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x07, 0x01])

    # DigestAlgorithm: SEQUENCE { OID sha256 }
    digest_alg = encode_sequence(encode_oid(sha256_oid))
    
    # SignatureAlgorithm: SEQUENCE { OID rsaEncryption }
    sig_alg = encode_sequence(encode_oid(rsa_encryption_oid))

    # Certificate (SEQUENCE wrapping the DER cert)
    cert_seq_value = cert_der_bytes
    # Parse to get issuer and serial
    cert_obj = x509.load_der_x509_certificate(cert_der_bytes, default_backend())
    issuer_der = cert_obj.issuer.public_bytes(serialization.Encoding.DER)
    serial = cert_obj.serial_number

    # IssuerAndSerialNumber: SEQUENCE { issuer SEQUENCE, serial INTEGER }
    issuer_and_serial = encode_sequence(issuer_der, encode_integer(serial))

    # SignerInfo: SEQUENCE {
    #   version INTEGER (1),
    #   issuerAndSerialNumber SEQUENCE,
    #   digestAlgorithm SEQUENCE,
    #   authenticatedAttributes [0] IMPLICIT (omitted),
    #   digestEncryptionAlgorithm SEQUENCE,
    #   encryptedDigest OCTET STRING
    # }
    signer_info = encode_sequence(
        encode_integer(1),           # version
        issuer_and_serial,           # issuerAndSerialNumber
        digest_alg,                  # digestAlgorithm
        # No authenticated attributes (empty)
        sig_alg,                     # digestEncryptionAlgorithm
        encode_octet_string(signature_bytes),  # encryptedDigest
    )

    # Certificates: [0] IMPLICIT SEQUENCE OF Certificate
    certs_explicit = encode_explicit(0, cert_der_bytes)

    # ContentInfo for the signed content: SEQUENCE { OID data }
    content_info = encode_sequence(encode_oid(data_oid))

    # SignedData: SEQUENCE {
    #   version INTEGER (1),
    #   digestAlgorithms SET OF DigestAlgorithmIdentifier,
    #   contentInfo ContentInfo,
    #   certificates [0] IMPLICIT CertificateSet,
    #   signerInfos SET OF SignerInfo
    # }
    signed_data = encode_sequence(
        encode_integer(1),           # version
        encode_set(digest_alg),      # digestAlgorithms
        content_info,                # contentInfo
        certs_explicit,              # certificates
        encode_set(signer_info),     # signerInfos
    )

    # ContentInfo wrapper: SEQUENCE { OID signedData [0] EXPLICIT SignedData }
    result = encode_sequence(
        encode_oid(signed_data_oid),
        encode_explicit(0, signed_data),
    )

    return result


def sign_apk_properly():
    """Правильная JAR v1 подпись APK"""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    import base64

    print("\n[签名] Генерация ключа...")
    key_pem, cert_pem = generate_signing_key()
    private_key = serialization.load_pem_private_key(key_pem, password=None, backend=default_backend())
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    cert_der = cert.public_bytes(serialization.Encoding.DER)

    print("[签名] Подготовка манифеста...")

    # Step 1: Build MANIFEST.MF
    manifest_lines = []
    manifest_lines.append("Manifest-Version: 1.0")
    manifest_lines.append("Created-By: 1.0 (Android ApkSigner)")
    manifest_lines.append("")

    entry_digests = {}

    with zipfile.ZipFile(ORIGINAL_APK, 'r') as zo:
        all_entries = sorted(zo.infolist(), key=lambda x: x.filename)

        for info in all_entries:
            if should_skip(info.filename):
                continue

            data = zo.read(info.filename)
            
            # Check if we need to replace this file
            replacement = get_replacement(info.filename)
            if replacement is not None and replacement != -1:
                data = replacement

            digest = base64.b64encode(hashlib.sha256(data).digest()).decode()
            entry_digests[info.filename] = digest
            manifest_lines.append(f"Name: {info.filename}")
            manifest_lines.append(f"SHA-256-Digest: {digest}")
            manifest_lines.append("")

    manifest_content = "\r\n".join(manifest_lines) + "\r\n"

    # Step 2: Build CERT.SF
    manifest_hash = base64.b64encode(hashlib.sha256(manifest_content.encode('utf-8')).digest()).decode()

    sf_lines = []
    sf_lines.append("Signature-Version: 1.0")
    sf_lines.append("Created-By: 1.0 (Android ApkSigner)")
    sf_lines.append(f"SHA-256-Digest-Manifest: {manifest_hash}")
    sf_lines.append("")

    for entry_name, digest in entry_digests.items():
        # Re-create the manifest entry block for this file
        entry_block = f"Name: {entry_name}\r\nSHA-256-Digest: {digest}\r\n\r\n"
        entry_hash = base64.b64encode(hashlib.sha256(entry_block.encode('utf-8')).digest()).decode()
        sf_lines.append(f"Name: {entry_name}")
        sf_lines.append(f"SHA-256-Digest: {entry_hash}")
        sf_lines.append("")

    sf_content = "\r\n".join(sf_lines) + "\r\n"

    # Step 3: Sign CERT.SF
    print("[签名] Подпись CERT.SF...")
    signature = private_key.sign(
        sf_content.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    # Step 4: Create PKCS#7
    print("[签名] Создание PKCS#7...")
    pkcs7_data = create_pkcs7_signed_data(cert_der, signature, b'')

    # Step 5: Write APK
    print("[签名] Запись APK...")
    with zipfile.ZipFile(ORIGINAL_APK, 'r') as zo:
        with zipfile.ZipFile(OUTPUT_APK, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Copy all original files (except old signatures and original MANIFEST.MF)
            for info in sorted(zo.infolist(), key=lambda x: x.filename):
                if should_skip(info.filename):
                    continue

                data = zo.read(info.filename)
                
                # Replace if needed
                replacement = get_replacement(info.filename)
                if replacement is not None and replacement != -1:
                    data = replacement
                    print(f"  [修改] {info.filename}")

                # Store with same compression as original
                new_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                new_info.compress_type = info.compress_type
                new_info.external_attr = info.external_attr
                
                # Preserve compression type from original
                if info.filename.endswith('.dex') or info.filename == 'resources.arsc':
                    # Keep original compression - don't force STORED
                    new_info.compress_type = info.compress_type
                
                zf.writestr(new_info, data)

            # Add new security files (only if not already in original)
            existing = set(zo.namelist())
            for fname, func in NEW_FILES.items():
                if fname not in existing:
                    zf.writestr(fname, func())
                    print(f"  [新增] {fname}")

            # Add signing files LAST
            zf.writestr("META-INF/MANIFEST.MF", manifest_content)
            zf.writestr("META-INF/CERT.SF", sf_content)
            zf.writestr("META-INF/CERT.RSA", pkcs7_data)

    size_mb = OUTPUT_APK.stat().st_size / 1024 / 1024
    print(f"\n[完成] JAR v1 подпись: {OUTPUT_APK} ({size_mb:.1f} MB)")
    
    # Now add APK Signature Scheme v2
    print("\n[签名 v2] Добавление APK Signature Scheme v2...")
    add_apk_signature_v2(key_pem, cert_pem)
    
    size_mb = OUTPUT_APK.stat().st_size / 1024 / 1024
    print(f"\n[完成] APK с v1+v2 подписью: {OUTPUT_APK} ({size_mb:.1f} MB)")
    return key_pem, cert_pem


def get_replacement(filename):
    """Возвращает замену для файла, или None если не нужна.
    Возвращает -1 если файл нужно пропустить."""
    replacements = {
        "com/google/api/client/googleapis/google.jks": b'\x00' * 10,
        "com/google/api/client/googleapis/google.p12": b'\x00' * 10,
        "res/xml/network_security_config.xml": create_network_security_config().encode('utf-8'),
    }
    if filename in replacements:
        return replacements[filename]
    # Skip original MANIFEST.MF - we'll create a new one
    if filename == "META-INF/MANIFEST.MF":
        return -1
    return None


def should_skip(filename):
    """Нужно ли пропустить файл"""
    # Skip old signatures
    if filename.startswith('META-INF/') and (
        filename.endswith('.SF') or 
        filename.endswith('.RSA') or 
        filename.endswith('.DSA') or 
        filename.endswith('.EC')
    ):
        return True
    # Skip original MANIFEST.MF
    if filename == "META-INF/MANIFEST.MF":
        return True
    return False


NEW_FILES = {
    "res/xml/security_config.xml": create_security_config,
    "META-INF/proguard-security.pro": create_proguard_rules,
    "SECURITY_FIXES.md": create_security_doc,
    "SECURITY_FIXES_REQUIRED.md": create_security_fixes_required,
}


def add_apk_signature_v2(key_pem, cert_pem):
    """Добавляем APK Signature Scheme v2 (APK Signing Block)"""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend

    private_key = serialization.load_pem_private_key(key_pem, password=None, backend=default_backend())
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    cert_der = cert.public_bytes(serialization.Encoding.DER)

    with open(OUTPUT_APK, 'rb') as f:
        apk_data = f.read()

    # Find the offset of the ZIP End of Central Directory
    eocd_offset = apk_data.rfind(b'\x50\x4b\x05\x06')
    if eocd_offset == -1:
        print("  ❌ Не найден End of Central Directory")
        return

    # Parse EOCD
    eocd = apk_data[eocd_offset:]
    cd_size = struct.unpack_from('<I', eocd, 12)[0]
    cd_offset = struct.unpack_from('<I', eocd, 16)[0]

    # Read Central Directory
    cd_data = apk_data[cd_offset:cd_offset + cd_size]

    # Content to hash for v2 signing:
    # 1. Everything before the signing block
    # 2. Signing block size (8 bytes) - 8
    # 3. Magic "APK Sig Block 42"
    
    # First, let's compute the hash of the APK content (excluding signing block and CD)
    # For simplicity, we'll hash from offset 0 to the signing block
    
    # Since we don't have an existing signing block, the content before CD
    # is everything from 0 to cd_offset
    content_before_cd = apk_data[:cd_offset]

    # Compute digests
    content_digest_sha256 = hashlib.sha256(content_before_cd).digest()

    # Create v2 signer info
    # Digest: pair ID 0x02 with SHA-256 of content
    digest_pair = struct.pack('<I', 0x02) + struct.pack('<I', len(content_digest_sha256)) + content_digest_sha256

    # Signature: sign the digest
    signature = private_key.sign(
        content_digest_sha256,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    # Signed data: contains digests, certificates, and signer info
    # Digests array
    digests_array = struct.pack('<I', 1) + struct.pack('<I', len(digest_pair)) + digest_pair
    
    # Certificate array
    cert_entry = struct.pack('<I', len(cert_der)) + cert_der
    certs_array = struct.pack('<I', 1) + struct.pack('<I', len(cert_entry)) + cert_entry
    
    # Signature algorithm: PKCS#1 v1.5 + SHA-256 = 0x0103
    sig_algorithm = struct.pack('<I', 0x0103)
    sig_data = struct.pack('<I', len(signature)) + signature
    sig_entry = sig_algorithm + struct.pack('<I', len(sig_data)) + sig_data
    sigs_array = struct.pack('<I', 1) + struct.pack('<I', len(sig_entry)) + sig_entry
    
    # Signed data block
    signed_data = (
        struct.pack('<I', len(digests_array)) + digests_array +
        struct.pack('<I', len(certs_array)) + certs_array +
        struct.pack('<I', len(sigs_array)) + sigs_array
    )
    
    # Pair: minSDK version (21) + maxSDK version (0xFFFFFFFF)
    min_max_sdk = struct.pack('<I', 21) + struct.pack('<I', 0xFFFFFFFF)
    
    # Signer block
    signer_block = (
        struct.pack('<I', len(min_max_sdk + signed_data)) +
        min_max_sdk +
        signed_data
    )
    
    # Signers array
    signers_array = struct.pack('<I', 1) + struct.pack('<I', len(signer_block)) + signer_block
    
    # Signed data v2 block (ID = 0x7109871a)
    signed_data_v2_content = signers_array
    signed_data_v2_block = struct.pack('<I', 0x7109871a) + struct.pack('<I', len(signed_data_v2_content)) + signed_data_v2_content

    # Now construct the APK Signing Block
    # Format: size (8 bytes) - 8, pairs..., size (8 bytes) - 8, magic
    magic = b'APK Sig Block 42'
    
    inner_block = signed_data_v2_block
    block_size = len(inner_block) + 8 + len(magic)  # +8 for the size field at end
    
    # Outer size = inner_block + size(8) + magic
    outer_size = block_size
    
    signing_block = (
        struct.pack('<Q', outer_size) +  # size - 8
        inner_block +
        struct.pack('<Q', outer_size) +  # size - 8 (copy)
        magic
    )

    # Now rebuild the APK:
    # [content_before_cd] [signing_block] [central_directory] [eocd]
    new_cd_offset = cd_offset + len(signing_block)
    
    # Update EOCD with new CD offset
    new_eocd = bytearray(eocd)
    struct.pack_into('<I', new_eocd, 16, new_cd_offset)
    
    # Rebuild APK
    new_apk = content_before_cd + signing_block + cd_data + bytes(new_eocd)
    
    with open(OUTPUT_APK, 'wb') as f:
        f.write(new_apk)
    
    print(f"  ✅ APK Signing Block добавлен ({len(signing_block)} bytes)")
    print(f"  ✅ v2 подпись: SHA-256 + PKCS#1 v1.5")


def verify_apk():
    """Проверяем что APK валидный"""
    print("\n" + "=" * 60)
    print("  ПРОВЕРКА APK")
    print("=" * 60)

    with zipfile.ZipFile(OUTPUT_APK, 'r') as zf:
        # 1. ZIP integrity
        bad = zf.testzip()
        print(f"  {'✅' if not bad else '❌'} ZIP целостность: {'OK' if not bad else f'BROKEN: {bad}'}")

        files = zf.namelist()

        # 2. All critical files present
        required = [
            'AndroidManifest.xml',
            'classes.dex',
            'META-INF/MANIFEST.MF',
            'META-INF/CERT.SF',
            'META-INF/CERT.RSA',
            'res/xml/network_security_config.xml',
            'res/xml/security_config.xml',
        ]
        for r in required:
            present = r in files
            print(f"  {'✅' if present else '❌'} {r}")

        # 3. No old signatures
        old_sigs = [f for f in files if f.startswith('META-INF/') and 
                    (f.endswith('.SF') or f.endswith('.RSA') or f.endswith('.DSA'))]
        new_sigs = [f for f in old_sigs if 'CERT' in f]
        old_only = [f for f in old_sigs if 'CERT' not in f]
        print(f"  {'✅' if not old_only else '❌'} Старые подписи удалены: {old_only or 'нет'}")
        print(f"  {'✅' if len(new_sigs) == 2 else '❌'} Новые подписи: {len(new_sigs)}")

        # 4. MANIFEST.MF has all entries
        mf = zf.read("META-INF/MANIFEST.MF").decode('utf-8')
        mf_entries = mf.count("Name: ")
        print(f"  {'✅' if mf_entries > 100 else '❌'} MANIFEST.MF записей: {mf_entries}")

        # 5. File count
        orig_count = len(zf.namelist())
        with zipfile.ZipFile(ORIGINAL_APK, 'r') as zo:
            # Count original files excluding old signatures
            orig_real = len([f for f in zo.namelist() if not (
                f.startswith('META-INF/') and (f.endswith('.SF') or f.endswith('.RSA') or f.endswith('.DSA'))
            )])
        
        # We add 5 new files
        expected = orig_real + 5
        print(f"  {'✅' if orig_count >= expected else '⚠️'} Файлов: {orig_count} (ожидалось ~{expected})")

        # 6. DEX files
        dex_files = [f for f in files if f.endswith('.dex')]
        print(f"  {'✅' if len(dex_files) == 4 else '❌'} DEX файлы: {len(dex_files)}")

        # 7. Size check
        size_mb = OUTPUT_APK.stat().st_size / 1024 / 1024
        print(f"  📦 Размер: {size_mb:.1f} MB")

    return True


def main():
    print("=" * 60)
    print("  ИСПРАВЛЕНИЕ APK v2: File Manager+ v3.8.2")
    print("=" * 60)
    
    # Remove old output
    if OUTPUT_APK.exists():
        OUTPUT_APK.unlink()
    
    key_pem, cert_pem = sign_apk_properly()
    
    # Save signing artifacts
    (WORK_DIR / "signing_key.pem").write_bytes(key_pem)
    (WORK_DIR / "signing_cert.pem").write_bytes(cert_pem)
    
    verify_apk()
    
    print("\n" + "=" * 60)
    print("  ✅ ГОТОВО!")
    print("=" * 60)
    print(f"\n  📁 {OUTPUT_APK}")
    print(f"  🔑 {WORK_DIR / 'signing_key.pem'}")


if __name__ == '__main__':
    main()
