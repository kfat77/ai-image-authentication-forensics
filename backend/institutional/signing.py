import hashlib, hmac
from dataclasses import dataclass
@dataclass(frozen=True)
class SignatureResult: report_hash: str; signature: str; algorithm: str; verification_status: str
class TestHmacReportSigner:
    __test__ = False
    algorithm="HMAC-SHA256-TEST-ONLY"
    def __init__(self, key: bytes) -> None: self._key=key
    def sign(self, report_hash: str) -> SignatureResult: return SignatureResult(report_hash,hmac.new(self._key,report_hash.encode(),hashlib.sha256).hexdigest(),self.algorithm,"valid")
    def verify(self, result: SignatureResult) -> bool: return hmac.compare_digest(self.sign(result.report_hash).signature,result.signature)
