"""
AES加密工具
    - aes_cfb_encrypt_base64: 使用 AES-CFB(128) 无填充对明文进行加密并返回 Base64 密文。
    - aes_cfb_decrypt_base64: 使用 AES-CFB(128) 无填充对 Base64 密文进行解密并返回明文。
"""
import base64
from Crypto.Cipher import AES

default_key = "PITWDjRNQCQ4xUev"
default_iv = "PITWDjRNQCQ4xUev"


def aes_cfb_encrypt_base64(
        plain_text: str,
        key: str = default_key,
        iv: str = default_iv,
        encoding: str = "utf-8") -> str:
    """
    使用 AES-CFB(128) 无填充对明文进行加密并返回 Base64 密文。
    参数:
        plain_text: 明文字符串（例如 "Aa123456"）
        key: 密钥字符串（长度需为 16/24/32 字节，对应 AES-128/192/256）
        iv: 初始向量字符串（长度需为 16 字节，CFB 与 CBC 相同要求）
        encoding: 文本、密钥与 IV 的编码（默认 UTF-8）
    返回:
        Base64 编码的密文字符串
    """
    k = key.encode(encoding)
    v = iv.encode(encoding)
    data = plain_text.encode(encoding)
    cipher = AES.new(k, AES.MODE_CFB, iv=v, segment_size=128)
    ct = cipher.encrypt(data)
    return base64.b64encode(ct).decode("ascii")


def aes_cfb_decrypt_base64(
        cipher_b64: str,
        key: str = default_key,
        iv: str = default_iv,
        encoding: str = "utf-8") -> str:
    """
    使用 AES-CFB(128) 无填充对 Base64 密文进行解密并返回明文。
    参数:
        cipher_b64: Base64 编码的密文字符串
        key: 密钥字符串
        iv: 初始向量字符串
        encoding: 文本、密钥与 IV 的编码（默认 UTF-8）
    返回:
        解密后的明文字符串
    """
    k = key.encode(encoding)
    v = iv.encode(encoding)
    ct = base64.b64decode(cipher_b64)
    cipher = AES.new(k, AES.MODE_CFB, iv=v, segment_size=128)
    pt = cipher.decrypt(ct)
    return pt.decode(encoding)


if __name__ == "__main__":
    text = "Szdm0808"

    ctext = aes_cfb_encrypt_base64(text)
    print("Cipher(Base64):", ctext)

    ptext = aes_cfb_decrypt_base64(ctext)
    print("Plain:", ptext)
