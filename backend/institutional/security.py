from enum import StrEnum
class Role(StrEnum): ADMIN="ADMIN"; ANALYST="ANALYST"; REVIEWER="REVIEWER"; AUDITOR="AUDITOR"
def require_role(actor_roles: set[Role], required: Role) -> None:
    if required not in actor_roles: raise PermissionError(f"{required} role is required.")
