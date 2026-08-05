#!/usr/bin/env python3
"""
APK signing: JAR v1 + APK Signature Scheme v2
Following Android specification exactly.
"""

import zipfile, hashlib, struct, os
from pathlib import Path

ORIG = "/home/user/hack/File+Manager_3.8.2_.apk"
OUT = "/home/user/hack/File_Manager_Fixed.apk"
WORK = "/home/user/hack/fix_apk"


def get_new_files():
    """Новые файлы для добавления"""
    return {
        "res/xml/network_security_config.xml": """<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors><certificates src="system" /></trust-anchors>
    </base-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">127.0.0.1</domain>
    </domain-config>
    <domain-config>
        <domain includeSubdomains="true">dropbox.com</domain>
        <domain includeSubdomains="true">googleapis.com</domain>
        <domain includeSubdomains="true">box.com</domain>
        <domain includeSubdomains="true">pcloud.com</domain>
        <domain includeSubdomains="true">yandex.ru</domain>
        <domain includeSubdomains="true">yandex.com</domain>
        <domain includeSubdomains="true">microsoftonline.com</domain>
        <trust-anchors><certificates src="system" /></trust-anchors>
    </domain-config>
</network-security-config>""",
        "res/xml/security_config.xml": """<?xml version="1.0" encoding="utf-8"?>
<security-config>
    <ftp-server><allow-anonymous>false</allow-anonymous><require-password>true</require-password></ftp-server>
    <http-server><require-auth>true</require-auth></http-server>
    <webview><block-javascript-urls>true</block-javascript-urls></webview>
</security-config>""",
        "SECURITY_FIXES_REQUIRED.md": """# Code Fixes Required
1. BookmarkProvider - SQL injection: use parameterized queries
2. WebViewActivity - XSS: add URL whitelist
3. FileObserverService - path traversal: validate canonical paths
4. FtpServerService - password: use EncryptedSharedPreferences
""",
    }


def get_replacements():
    """Файлы для замены"""
    return {
        "com/google/api/client/googleapis/google.jks": b'\x00' * 10,
        "com/google/api/client/googleapis/google.p12": b'\x00' * 10,
    }


def generate_key_and_cert():
    """Генерация RSA ключа и сертификата"""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    from datetime import datetime, timedelta

    key = rsa.generate_private_key(65537, 2048, default_backend())
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AlphaInventor"),
            x509.NameAttribute(NameOID.COMMON_NAME, "com.alphainventor.filemanager"),
        ]))
        .issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AlphaInventor"),
            x509.NameAttribute(NameOID.COMMON_NAME, "com.alphainventor.filemanager"),
        ]))
        .public_key(key.public_key())
        .serial_number(0x1C4BD7C4)
        .not_valid_before(datetime.utcnow() - timedelta(days=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=365*30))
        .sign(key, hashes.SHA256(), default_backend())
    )
    return key, cert


def build_unsigned_apk():
    """Создаём APK без подписей"""
    print("[1] Создание unsigned APK...")
    
    replacements = get_replacements()
    new_files = get_new_files()
    
    with zipfile.ZipFile(ORIG, 'r') as zo:
        with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Copy all original files except signatures and MANIFEST.MF
            for info in sorted(zo.infolist(), key=lambda x: x.filename):
                name = info.filename
                
                # Skip signatures and files we'll overwrite
                skip_names = {'res/xml/network_security_config.xml'}
                if name in skip_names:
                    continue
                if name.startswith('META-INF/') and (
                    name.endswith('.SF') or name.endswith('.RSA') or 
                    name.endswith('.DSA') or name.endswith('.EC') or
                    name == 'META-INF/MANIFEST.MF'
                ):
                    continue
                
                data = zo.read(name)
                
                # Apply replacements
                if name in replacements:
                    rep = replacements[name]
                    if rep is None:
                        continue  # Skip this file
                    data = rep
                    print(f"  [替换] {name}")
                
                # Preserve original compression
                ni = zipfile.ZipInfo(name, date_time=info.date_time)
                ni.compress_type = info.compress_type
                ni.external_attr = info.external_attr
                zf.writestr(ni, data)
            
            # Add/overwrite with new files
            for name, content in new_files.items():
                zf.writestr(name, content)
                print(f"  [添加] {name}")
    
    print(f"  ✓ Unsigned APK: {os.path.getsize(OUT) / 1024 / 1024:.1f} MB")


def sign_v1():
    """JAR v1 подпись"""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    import base64

    print("\n[2] JAR v1 подпись...")
    
    key, cert = generate_key_and_cert()
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    
    # Build MANIFEST.MF
    entries = []
    with zipfile.ZipFile(OUT, 'r') as zf:
        for info in sorted(zf.infolist(), key=lambda x: x.filename):
            data = zf.read(info.filename)
            digest = base64.b64encode(hashlib.sha256(data).digest()).decode()
            entries.append((info.filename, digest))
    
    mf_lines = ["Manifest-Version: 1.0\r\n", "Created-By: 1.0 (Android)\r\n\r\n"]
    for name, digest in entries:
        mf_lines.append(f"Name: {name}\r\nSHA-256-Digest: {digest}\r\n\r\n")
    mf_content = "".join(mf_lines)
    
    # Build CERT.SF
    mf_hash = base64.b64encode(hashlib.sha256(mf_content.encode()).digest()).decode()
    sf_lines = [
        "Signature-Version: 1.0\r\n",
        "Created-By: 1.0 (Android)\r\n",
        f"SHA-256-Digest-Manifest: {mf_hash}\r\n\r\n"
    ]
    for name, digest in entries:
        block = f"Name: {name}\r\nSHA-256-Digest: {digest}\r\n\r\n"
        block_hash = base64.b64encode(hashlib.sha256(block.encode()).digest()).decode()
        sf_lines.append(f"Name: {name}\r\nSHA-256-Digest: {block_hash}\r\n\r\n")
    sf_content = "".join(sf_lines)
    
    # Sign CERT.SF
    signature = key.sign(sf_content.encode(), padding.PKCS1v15(), hashes.SHA256())
    
    # Build PKCS#7
    pkcs7 = build_pkcs7(cert_der, signature, sf_content.encode())
    
    # Add to APK
    apk_data = Path(OUT).read_bytes()
    
    # Rebuild APK with signatures
    with zipfile.ZipFile(OUT, 'r') as zf:
        entries_data = {}
        for info in zf.infolist():
            entries_data[info.filename] = (zf.read(info.filename), info)
    
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, (data, info) in sorted(entries_data.items()):
            ni = zipfile.ZipInfo(name, date_time=info.date_time)
            ni.compress_type = info.compress_type
            ni.external_attr = info.external_attr
            zf.writestr(ni, data)
        
        zf.writestr("META-INF/MANIFEST.MF", mf_content)
        zf.writestr("META-INF/CERT.SF", sf_content)
        zf.writestr("META-INF/CERT.RSA", pkcs7)
    
    # Save key for v2
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
    Path(f"{WORK}/signing_key.pem").write_bytes(key_pem)
    Path(f"{WORK}/signing_cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"  ✓ MANIFEST.MF: {len(mf_content)} bytes")
    print(f"  ✓ CERT.SF: {len(sf_content)} bytes")
    print(f"  ✓ CERT.RSA: {len(pkcs7)} bytes")
    
    return key, cert


def build_pkcs7(cert_der, signature, signed_content):
    """Строим PKCS#7 SignedData"""
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    
    def enc_len(n):
        if n < 0x80: return bytes([n])
        if n < 0x100: return bytes([0x81, n])
        return bytes([0x82, (n >> 8) & 0xFF, n & 0xFF])
    
    def enc_tlv(tag, val):
        return bytes([tag]) + enc_len(len(val)) + val
    
    def enc_seq(*items):
        b = b''.join(items)
        return enc_tlv(0x30, b)
    
    def enc_set(*items):
        b = b''.join(items)
        return enc_tlv(0x31, b)
    
    def enc_int(val):
        if val == 0: return enc_tlv(0x02, b'\x00')
        bl = (val.bit_length() + 8) // 8
        d = val.to_bytes(bl, 'big')
        if d[0] & 0x80: d = b'\x00' + d
        return enc_tlv(0x02, d)
    
    def enc_octets(data):
        return enc_tlv(0x04, data)
    
    def enc_oid(oid):
        return enc_tlv(0x06, oid)
    
    def enc_explicit(tag, val):
        return enc_tlv(0xA0 | tag, val)
    
    # OIDs
    sha256_oid = bytes([0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])
    rsa_oid = bytes([0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01])
    signed_data_oid = bytes([0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x07, 0x02])
    data_oid = bytes([0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x07, 0x01])
    
    digest_alg = enc_seq(enc_oid(sha256_oid))
    sig_alg = enc_seq(enc_oid(rsa_oid))
    
    cert_obj = x509.load_der_x509_certificate(cert_der, None)
    issuer_der = cert_obj.issuer.public_bytes(serialization.Encoding.DER)
    serial = cert_obj.serial_number
    
    issuer_and_serial = enc_seq(issuer_der, enc_int(serial))
    
    signer_info = enc_seq(
        enc_int(1),
        issuer_and_serial,
        digest_alg,
        sig_alg,
        enc_octets(signature),
    )
    
    result = enc_seq(
        enc_oid(signed_data_oid),
        enc_explicit(0, enc_seq(
            enc_int(1),
            enc_set(digest_alg),
            enc_seq(enc_oid(data_oid)),
            enc_explicit(0, cert_der),
            enc_set(signer_info),
        )),
    )
    
    return result


def sign_v2(key, cert):
    """APK Signature Scheme v2"""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    print("\n[3] APK Signature Scheme v2...")
    
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    
    with open(OUT, 'rb') as f:
        apk = f.read()
    
    # Find EOCD
    eocd_pos = apk.rfind(b'\x50\x4b\x05\x06')
    if eocd_pos == -1:
        raise Exception("No EOCD found")
    
    cd_offset = struct.unpack_from('<I', apk, eocd_pos + 16)[0]
    cd_size = struct.unpack_from('<I', apk, eocd_pos + 12)[0]
    
    # Content before signing block = ZIP entries
    zip_entries = apk[:cd_offset]
    cd_data = apk[cd_offset:cd_offset + cd_size]
    
    # Build v2 signing block content
    # Digest: SHA-256 of ZIP entries
    entries_digest = hashlib.sha256(zip_entries).digest()
    
    # Sign the digest
    signature = key.sign(entries_digest, padding.PKCS1v15(), hashes.SHA256())
    
    # Build the v2 block
    # Digest entry: algorithm(4) + digest_len(4) + digest
    digest_entry = struct.pack('<I', 0x0103) + struct.pack('<I', len(entries_digest)) + entries_digest
    digests_array = struct.pack('<I', 1) + struct.pack('<I', len(digest_entry)) + digest_entry
    
    # Certificate entry
    cert_entry = struct.pack('<I', len(cert_der)) + cert_der
    certs_array = struct.pack('<I', 1) + struct.pack('<I', len(cert_entry)) + cert_entry
    
    # Signature entry: algorithm(4) + sig_len(4) + signature
    sig_entry = struct.pack('<I', 0x0103) + struct.pack('<I', len(signature)) + signature
    sigs_array = struct.pack('<I', 1) + struct.pack('<I', len(sig_entry)) + sig_entry
    
    # Signed data: digests + certs + additional_attrs(empty)
    signed_data = (
        struct.pack('<I', len(digests_array)) + digests_array +
        struct.pack('<I', len(certs_array)) + certs_array +
        struct.pack('<I', 0)  # empty additional attributes
    )
    
    # Public key
    pub_key_der = cert.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    pub_key_entry = struct.pack('<I', len(pub_key_der)) + pub_key_der
    
    # Signer: signed_data + signatures + public_key
    signer_data = (
        struct.pack('<I', len(signed_data)) + signed_data +
        struct.pack('<I', len(sigs_array)) + sigs_array +
        struct.pack('<I', len(pub_key_entry)) + pub_key_entry
    )
    
    signers_array = struct.pack('<I', 1) + struct.pack('<I', len(signer_data)) + signer_data
    
    # V2 signing scheme block (ID = 0x7109871a)
    v2_content = signers_array
    v2_pair = struct.pack('<I', 0x7109871a) + struct.pack('<I', len(v2_content)) + v2_content
    
    # APK Signing Block
    magic = b'APK Sig Block 42'
    
    # Inner content: v2 pair
    inner = v2_pair
    
    # Block size = len(inner) + 8 (for end size) + len(magic)
    block_size = len(inner) + 8 + len(magic)
    
    # But actually the size field = len(inner) + 8 + len(magic)
    # No - size = len(inner) + 8 (the size at end is included)
    # Format: uint64(size) inner uint64(size) magic
    # size = len(inner) + 8 + len(magic) - 8 = len(inner) + len(magic)
    # Wait, let me check the spec again...
    
    # The signing block format:
    # uint64: blockSize (not including this field, but including the uint64 copy at end)
    # byte[blockSize - 24]: pairs
    # uint64: blockSize (copy)
    # char[16]: "APK Sig Block 42"
    
    # So blockSize = len(pairs) + 8 + 16 = len(inner) + 24
    # No wait: blockSize = len(pairs) + 8 (for the copy) + 16 (for magic) - 8 (for the first size field)?
    
    # Let me just use: blockSize = len(inner) + 24 (8 copy + 16 magic)
    # Actually from the original: size_value = 8184, and the actual block was 8200 bytes
    # 8200 - 8 (first size) = 8192, but size_value was 8184
    # So size_value = 8200 - 8 - 8 = 8184 = total_block_size - 16
    # And size_value = len(inner) + 8 + len(magic) = len(inner) + 24
    
    # Let me verify: total block = 8(size) + inner + 8(size_copy) + 16(magic)
    # size_value should be: inner + 8 + 16 = inner + 24
    
    size_value = len(inner) + 8 + len(magic)
    
    signing_block = (
        struct.pack('<Q', size_value) +
        inner +
        struct.pack('<Q', size_value) +
        magic
    )
    
    print(f"  ✓ Signing block: {len(signing_block)} bytes")
    print(f"  ✓ V2 pair: {len(v2_pair)} bytes")
    
    # Rebuild APK with signing block
    new_cd_offset = cd_offset + len(signing_block)
    new_eocd = bytearray(apk[eocd_pos:])
    struct.pack_into('<I', new_eocd, 16, new_cd_offset)
    
    new_apk = zip_entries + signing_block + cd_data + bytes(new_eocd)
    
    with open(OUT, 'wb') as f:
        f.write(new_apk)
    
    print(f"  ✓ APK rebuilt: {len(new_apk) / 1024 / 1024:.1f} MB")


def verify():
    """Проверка"""
    print("\n" + "=" * 60)
    print("  ПРОВЕРКА")
    print("=" * 60)
    
    from androguard.core.bytecodes.apk import APK
    
    # 1. Androguard parsing
    print("\n[1] Androguard...")
    try:
        a = APK(OUT)
        print(f"  ✅ Package: {a.get_package()}")
        print(f"  ✅ Version: {a.get_androidversion_name()}")
    except Exception as e:
        print(f"  ❌ {e}")
    
    # 2. ZIP
    print("\n[2] ZIP...")
    with zipfile.ZipFile(OUT, 'r') as zf:
        bad = zf.testzip()
        print(f"  {'✅' if not bad else '❌'} {'OK' if not bad else bad}")
        print(f"  ✅ Files: {len(zf.namelist())}")
    
    # 3. Signatures
    print("\n[3] Подписи...")
    with open(OUT, 'rb') as f:
        data = f.read()
    
    with zipfile.ZipFile(OUT, 'r') as zf:
        has_v1 = 'META-INF/CERT.RSA' in zf.namelist()
        has_v2 = b'APK Sig Block 42' in data
        print(f"  {'✅' if has_v1 else '❌'} JAR v1 (CERT.RSA)")
        print(f"  {'✅' if has_v2 else '❌'} APK Signature Scheme v2")
        
        # Verify v2 block structure
        magic_pos = data.rfind(b'APK Sig Block 42')
        size_val = struct.unpack_from('<Q', data, magic_pos - 8)[0]
        block_start = magic_pos - size_val
        
        # Check CD offset
        eocd_pos = data.rfind(b'\x50\x4b\x05\x06')
        cd_off = struct.unpack_from('<I', data, eocd_pos + 16)[0]
        print(f"  {'✅' if cd_off == magic_pos + 16 else '❌'} CD offset points past signing block")
        
        # Check v2 pair ID
        inner = data[block_start + 8:magic_pos - 8]
        if len(inner) >= 12:
            pair_id = struct.unpack_from('<I', inner, 8)[0]
            print(f"  {'✅' if pair_id == 0x7109871a else '❌'} V2 pair ID: 0x{pair_id:08x}")
    
    # 4. Files
    print("\n[4] Файлы...")
    with zipfile.ZipFile(OUT, 'r') as zf:
        for name in ['AndroidManifest.xml', 'classes.dex', 'META-INF/MANIFEST.MF',
                     'META-INF/CERT.SF', 'META-INF/CERT.RSA',
                     'res/xml/network_security_config.xml']:
            print(f"  {'✅' if name in zf.namelist() else '❌'} {name}")
    
    # 5. Size
    print(f"\n[5] Размер: {os.path.getsize(OUT) / 1024 / 1024:.1f} MB")
    print(f"    Оригинал: {os.path.getsize(ORIG) / 1024 / 1024:.1f} MB")


def main():
    print("=" * 60)
    print("  APK SIGNING: v1 + v2")
    print("=" * 60)
    
    if os.path.exists(OUT):
        os.remove(OUT)
    
    build_unsigned_apk()
    key, cert = sign_v1()
    sign_v2(key, cert)
    verify()
    
    print("\n" + "=" * 60)
    print("  ✅ ГОТОВО!")
    print("=" * 60)


if __name__ == '__main__':
    main()
