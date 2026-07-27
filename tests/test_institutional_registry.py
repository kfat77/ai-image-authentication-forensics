from hashlib import sha256
from io import BytesIO
import pytest
from PIL import Image
from deployment.key_provider import LocalTestKeyProvider
from institutional_registry import ApprovalStatus, InstitutionalRegistry, verify_registry_record
from authentication import AuthenticationReportEngine

H="a"*64
def _registry(): return InstitutionalRegistry(LocalTestKeyProvider(b"registry-test-key"))
def _model_payload(): return {"model_id":"m","version":"v1","architecture":"linear","weight_hash":H,"source":"official","license":"BSD","training_data_reference":"dataset","evaluation_reference":"evaluation","calibration_id":"c1","provider_id":"ml.m"}
def _calibration_payload(): return {"calibration_id":"c1","model_id":"m","dataset_reference":"dataset","method":"temperature","metrics":{"ece":0.1},"threshold":0.5,"scope":["JPEG_FILE"],"limitations":["bounded"]}
def _approved(registry):
 m=registry.create_model(_model_payload(),"submitter"); c=registry.create_calibration(_calibration_payload(),"submitter")
 for state in (ApprovalStatus.SUBMITTED,ApprovalStatus.VALIDATED,ApprovalStatus.REVIEWED,ApprovalStatus.APPROVED): m=registry.transition(m.record_hash,state,"approver" if state==ApprovalStatus.APPROVED else "validator","reason")
 for state in (ApprovalStatus.SUBMITTED,ApprovalStatus.VALIDATED,ApprovalStatus.REVIEWED,ApprovalStatus.APPROVED): c=registry.transition(c.record_hash,state,"approver" if state==ApprovalStatus.APPROVED else "validator","reason")
 return m,c
def _png():
 out=BytesIO();Image.new("RGB",(8,8)).save(out,format="PNG");return out.getvalue()
def test_tampering_and_signature_verification_fail():
 r=_registry(); record=r.create_model(_model_payload(),"submitter")
 assert r.verify_record(record.record_hash)
 tampered=record.__class__(record.record_type,{**record.payload,"source":"changed"},record.record_hash,record.signature)
 assert not verify_registry_record(tampered,{record.signature.key_id:LocalTestKeyProvider(b"registry-test-key")})
def test_workflow_separation_and_provider_binding():
 r=_registry(); draft=r.create_model(_model_payload(),"submitter")
 with pytest.raises(PermissionError):
  x=draft
  for state in (ApprovalStatus.SUBMITTED,ApprovalStatus.VALIDATED,ApprovalStatus.REVIEWED,ApprovalStatus.APPROVED): x=r.transition(x.record_hash,state,"submitter","reason")
 m,c=_approved(r); admission=r.admit_provider("ml.m","v1",m.record_hash,c.record_hash,("JPEG_FILE",))
 assert verify_registry_record(admission,{admission.signature.key_id:LocalTestKeyProvider(b"registry-test-key")})
 with pytest.raises(ValueError): r.admit_provider("wrong","v1",m.record_hash,c.record_hash,("JPEG_FILE",))
def test_report_carries_reproducibility_references(tmp_path):
 r=_registry();m,c=_approved(r);p=r.admit_provider("ml.m","v1",m.record_hash,c.record_hash,("JPEG_FILE",))
 report=AuthenticationReportEngine().create(_png(),tmp_path,"reviewer",registry_references={"model_record_hash":m.record_hash,"calibration_record_hash":c.record_hash,"provider_record_hash":p.record_hash})
 assert report.evidence["registry_references"]["provider_record_hash"]==p.record_hash
