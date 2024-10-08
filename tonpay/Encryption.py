class Symmetric:
    def __init__(self, key: str) -> None:
        from wolfcrypt.ciphers import Aes, MODE_CBC
        max_len = 16
        if len(key) > max_len: key = key[:max_len]
        self.cipher = Aes(key, MODE_CBC, key)
       
        
    def encrypt(self, input_str: str)-> bytes:
        while len(input_str)%16 != 0: input_str += ' '
        enc_text = self.cipher.encrypt(input_str)
        return enc_text
    
    
    def decrypt(self, input_str: str|bytes):
        dec_text = self.cipher.decrypt(input_str).decode().strip()
        return dec_text
    
    
def SHA256(input_str: str):
    from hashlib import sha256
    sha256_txt = sha256(input_str.encode('utf-8')).hexdigest()
    return sha256_txt

    
def RSA_Private(private_key:str):
    from wolfcrypt.ciphers import RsaPrivate
    return RsaPrivate(private_key)


def RSA_Public(public_key:str):
    from wolfcrypt.ciphers import RsaPublic
    return RsaPublic(public_key)
        
    
def generate_keyPairs(bits:int = 2048):
    """generate public and private keys

    Args:
        bits (int, optional): Defaults to 2048.

    Returns:
        tuple[private_key, public_key]
    """    
    from Crypto.PublicKey import RSA

    key = RSA.generate(bits)
    private_key = key.export_key("DER")
    public_key = key.publickey().export_key("DER")
    return private_key, public_key


def toBASE64(input_str: str):
    import base64 
    sample_string_bytes = input_str.encode("ascii") 
    base64_bytes = base64.b64encode(sample_string_bytes) 
    return base64_bytes


def fromBASE64(input_str: str|bytes):
    import base64
    if not isinstance(input_str, bytes): input_str = input_str.encode("ascii")
    res = base64.b64decode(input_str).decode()
    return res
