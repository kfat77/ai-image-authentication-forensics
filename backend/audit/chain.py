from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
@dataclass(frozen=True)
class AuditEvent: event_id:str; timestamp:str; actor:str; action:str; case_id:str; input_hash:str; output_hash:str; previous_event_hash:str|None
def _hash(event:AuditEvent)->str:return sha256(json.dumps(asdict(event),sort_keys=True,separators=(",",":")).encode()).hexdigest()
class AuditLog:
 def __init__(self)->None:self.events:list[AuditEvent]=[]
 def append(self,actor:str,action:str,case_id:str,input_hash:str,output_hash:str)->AuditEvent:
  event=AuditEvent(str(len(self.events)+1),datetime.now(timezone.utc).isoformat(),actor,action,case_id,input_hash,output_hash,_hash(self.events[-1]) if self.events else None);self.events.append(event);return event
def verify_audit_chain(events:list[AuditEvent])->dict[str,object]:
 previous=None
 for event in events:
  if event.previous_event_hash!=previous:return {"status":"broken_event","broken_event":event.event_id}
  previous=_hash(event)
 return {"status":"valid","broken_event":None}
