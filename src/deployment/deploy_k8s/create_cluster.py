import pulumi
import pulumi_gcp as gcp
from pulumi import ResourceOptions, Output
import pulumi_kubernetes as k8s
import pulumi_command as command
import yaml

base_config = pulumi.Config()
service_account_email = pulumi.Config("security").get("gcp_service_account_email")
ksa_service_account_email = pulumi.Config("security").get("gcp_ksa_service_account_email")

# Keep this small to avoid quota surprises.
initial_node_count = 2
machine_type = "e2-highmem-8"
machine_disk_size = 50  # GB
machine_disk_type = "pd-standard"  # Avoid SSD quota pressure

def _region_to_zone(loc: str) -> str:
    """
    If user passes a region like 'us-central1', convert to a zone like 'us-central1-a'.
    If they already passed a zone like 'us-central1-b', keep it.
    """
    loc = (loc or "").strip()
    # Regions typically look like "us-central1" (1 hyphen).
    # Zones typically look like "us-central1-a" (2 hyphens).
    if loc.count("-") == 1:
        return f"{loc}-a"
    return loc

def create_cluster(project, region, network, subnet, app_name):
    zone = _region_to_zone(region)

    # -----------------------------
    # GKE cluster (ZONAL to avoid regional multi-zone node multiplication)
    # -----------------------------
    cluster = gcp.container.Cluster(
        f"{app_name}-cluster",
        name=f"{app_name}-cluster",
        description="GKE cluster",
        location=zone,  # IMPORTANT: zone, not region
        deletion_protection=False,
        network=network.name,
        subnetwork=subnet.name,

        # Remove default pool; keep initial_node_count minimal (API requires it).
        remove_default_node_pool=True,
        initial_node_count=1,

        private_cluster_config={
            "enable_private_nodes": True,
            "enable_private_endpoint": False,
            "master_ipv4_cidr_block": "172.0.0.0/28",
        },
        workload_identity_config={
            "workload_pool": f"{project}.svc.id.goog",
        },
        gateway_api_config={
            "channel": "CHANNEL_STANDARD",
        },
    )

    # -----------------------------
    # Custom node pool
    # -----------------------------
    node_pool = gcp.container.NodePool(
        f"{app_name}-pool",
        cluster=cluster.name,
        location=zone,  # IMPORTANT: zone, not region
        initial_node_count=initial_node_count,
        node_config=gcp.container.NodePoolNodeConfigArgs(
            service_account=service_account_email,
            machine_type=machine_type,
            image_type="cos_containerd",
            disk_size_gb=machine_disk_size,
            disk_type=machine_disk_type,
            oauth_scopes=[
                "https://www.googleapis.com/auth/devstorage.read_only",
                "https://www.googleapis.com/auth/logging.write",
                "https://www.googleapis.com/auth/monitoring",
                "https://www.googleapis.com/auth/servicecontrol",
                "https://www.googleapis.com/auth/service.management.readonly",
                "https://www.googleapis.com/auth/trace.append",
            ],
        ),
        autoscaling=gcp.container.NodePoolAutoscalingArgs(
            min_node_count=2,
            max_node_count=3,
        ),
        management=gcp.container.NodePoolManagementArgs(
            auto_repair=True,
            auto_upgrade=True,
        ),
    )

    # -----------------------------
    # Kubeconfig for k8s provider
    # -----------------------------
    k8s_info = Output.all(cluster.name, cluster.endpoint, cluster.master_auth)

    def make_kubeconfig(info):
        cluster_name, endpoint, master_auth = info
        context_name = f"{project}_{zone}_{cluster_name}"

        # master_auth may be an object-like dict; handle both safely
        ca = None
        if isinstance(master_auth, dict):
            ca = master_auth.get("cluster_ca_certificate") or master_auth.get("clusterCaCertificate")
        else:
            ca = getattr(master_auth, "cluster_ca_certificate", None) or getattr(master_auth, "clusterCaCertificate", None)

        if not ca:
            raise Exception("Could not read cluster CA certificate from cluster.master_auth")

        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "name": context_name,
                    "cluster": {
                        "certificate-authority-data": ca,
                        "server": f"https://{endpoint}",
                    },
                }
            ],
            "contexts": [
                {
                    "name": context_name,
                    "context": {"cluster": context_name, "user": context_name},
                }
            ],
            "current-context": context_name,
            "users": [
                {
                    "name": context_name,
                    "user": {
                        "exec": {
                            "apiVersion": "client.authentication.k8s.io/v1beta1",
                            "command": "gke-gcloud-auth-plugin",
                            "installHint": "Install gke-gcloud-auth-plugin for use with kubectl",
                            "provideClusterInfo": True,
                            "interactiveMode": "Never",
                        }
                    },
                }
            ],
        }

        return yaml.dump(kubeconfig, default_flow_style=False)

    cluster_kubeconfig = k8s_info.apply(make_kubeconfig)

    k8s_provider = k8s.Provider(
        "gke_k8s_v2",
        kubeconfig=cluster_kubeconfig,
        opts=ResourceOptions(depends_on=[node_pool]),
    )

    namespace = k8s.core.v1.Namespace(
        f"{app_name}-namespace",
        metadata={"name": f"{app_name}-namespace"},
        opts=ResourceOptions(provider=k8s_provider),
    )

    # --- Kubernetes Service Account (KSA) with Workload Identity annotation ---
    ksa_name = "api-ksa"
    api_ksa = k8s.core.v1.ServiceAccount(
        "api-ksa",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=ksa_name,
            namespace=namespace.metadata["name"],
            annotations={
                "iam.gke.io/gcp-service-account": f"{ksa_service_account_email}",
            },
        ),
        opts=ResourceOptions(provider=k8s_provider),
    )

    project_id = gcp.config.project
    wi_member = Output.concat(
        "serviceAccount:",
        project_id,
        ".svc.id.goog[",
        namespace.metadata["name"],
        "/",
        ksa_name,
        "]",
    )

    gsa_full_id = Output.concat(
        "projects/", project_id, "/serviceAccounts/", f"{ksa_service_account_email}"
    )

    gsa_wi_binding_strict = gcp.serviceaccount.IAMMember(
        "api-gsa-wi-user",
        service_account_id=gsa_full_id,
        role="roles/iam.workloadIdentityUser",
        member=wi_member,
    )

    # Optional: connect kubectl context locally (now uses --zone)
    connect_k8s_command = command.local.Command(
        "connect-k8s-command",
        create=Output.concat(
            "gcloud container clusters get-credentials ",
            cluster.name,
            f" --zone {zone} --project {project}"
        ),
        opts=ResourceOptions(depends_on=[cluster, node_pool]),
    )

    return cluster, namespace, k8s_provider, ksa_name
