from cases import CaseRepository, CaseState
from evidence_storage.preservation import EvidencePreservationStore, PreservedEvidence
from institutional import Role, TestHmacReportSigner, require_role
from audit import AuditLog, verify_audit_chain
import pytest
H="a"*64
def test_case_lifecycle_and_separation():
 r=CaseRepository(); c=r.create(H,"analyst"); c=r.advance(c.case_id,CaseState.EVIDENCE_COLLECTED,evidence_bundle_hash=H); c=r.advance(c.case_id,CaseState.UNDER_REVIEW)
 with pytest.raises(ValueError):r.advance(c.case_id,CaseState.REPORT_GENERATED,report_hash=H,reviewer="analyst")
 assert r.advance(c.case_id,CaseState.REPORT_GENERATED,report_hash=H,reviewer="reviewer").state==CaseState.REPORT_GENERATED
def test_rbac_evidence_audit_and_signature():
 with pytest.raises(PermissionError):require_role({Role.ANALYST},Role.REVIEWER)
 s=EvidencePreservationStore();s.preserve(PreservedEvidence("c",H,H,None))
 with pytest.raises(ValueError):s.preserve(PreservedEvidence("c","b"*64,H,None))
 log=AuditLog();log.append("a","submit","c",H,H);log.append("r","review","c",H,H);assert verify_audit_chain(log.events)["status"]=="valid";log.events[1]=log.events[1].__class__(**{**log.events[1].__dict__,"previous_event_hash":H});assert verify_audit_chain(log.events)["status"]=="broken_event"
 signer=TestHmacReportSigner(b"test");assert signer.verify(signer.sign(H))
