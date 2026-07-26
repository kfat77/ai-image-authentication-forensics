from pathlib import Path

import yaml


MANIFESTS = Path(__file__).parents[1] / "k8s" / "base"


def load_manifest(name: str) -> dict:
    return yaml.safe_load((MANIFESTS / name).read_text(encoding="utf-8"))


def test_deployment_has_restricted_runtime_and_ephemeral_upload_storage() -> None:
    deployment = load_manifest("deployment.yaml")
    pod_spec = deployment["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]
    assert pod_spec["automountServiceAccountToken"] is False
    assert pod_spec["securityContext"]["runAsNonRoot"] is True
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert container["securityContext"]["capabilities"]["drop"] == ["ALL"]
    assert pod_spec["volumes"][0]["emptyDir"]["medium"] == "Memory"
    assert all("value" not in env or "SECRET" not in env["name"] for env in container["env"])
    env = {item["name"]: item for item in container["env"]}
    assert env["APP_VISION_PROVIDER_URL"]["valueFrom"]["configMapKeyRef"]["optional"] is True
    assert env["APP_VISION_PROVIDER_TOKEN"]["valueFrom"]["secretKeyRef"]["optional"] is True


def test_network_policy_limits_ingress_and_egress() -> None:
    policy = load_manifest("network-policy.yaml")
    assert policy["spec"]["policyTypes"] == ["Ingress", "Egress"]
    assert policy["spec"]["ingress"]
    assert policy["spec"]["egress"]
