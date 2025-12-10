import os
from pathlib import Path

import pulumi
import pulumi_kubernetes as k8s


def setup_containers(project, namespace, k8s_provider, ksa_name, app_name):
    deploy_config = pulumi.Config("deploy-k8s")

    stack_ref_name = (
        deploy_config.get("imagesStackRef")
        or os.getenv("PULUMI_IMAGES_STACK")
        or "organization/deploy-images/dev"
    )
    images_stack = pulumi.StackReference(stack_ref_name)

    def latest_tag(output_name: str):
        tags = images_stack.require_output(output_name)
        return tags.apply(lambda arr: arr[-1])

    frontend_image = latest_tag("finwhiz-frontend-tags")
    agent_image = latest_tag("finwhiz-agent-tags")
    llm_image = latest_tag("finwhiz-llm-tags")

    def cfg(key: str, default: str, env_var: str | None = None):
        if env_var:
            env_val = os.getenv(env_var)
            if env_val:
                return env_val
        return deploy_config.get(key) or default

    def cfg_secret(key: str, env_var: str | None = None):
        if env_var:
            env_val = os.getenv(env_var)
            if env_val:
                return env_val
        return deploy_config.get_secret(key)

    project_root = Path(__file__).resolve().parents[3]
    candidate_secret_dirs = [
        project_root / "secrets",
        Path("/secrets"),
    ]
    secrets_dir = None
    for candidate in candidate_secret_dirs:
        if candidate.exists():
            secrets_dir = candidate
            break
    if secrets_dir is None:
        secrets_dir = project_root / "secrets"

    gcs_bucket = cfg("gcsBucket", "finwhiz-storage", env_var="GCS_BUCKET")
    # gcs_prefix = cfg("gcsPrefix", "chroma_storage", env_var="GCS_PREFIX")
    gcs_prefix = cfg("gcsPrefix", "chroma_storage_backup", env_var="GCS_PREFIX")

    user_upload_bucket = cfg(
        "userUploadBucket", "fw_user_uploads", env_var="USER_UPLOAD_BUCKET"
    )
    database_url = cfg(
        "databaseUrl",
        "postgresql+psycopg://finwhiz:finwhiz@cloudsql-proxy:5432/finwhiz",
        env_var="DATABASE_URL",
    )
    db_user = cfg("dbUser", "postgres", env_var="DB_USER")
    db_name = cfg("dbName", "postgres", env_var="DB_NAME")
    db_host = cfg("dbHost", "cloudsql-proxy", env_var="DB_HOST")
    db_port = cfg("dbPort", "5432", env_var="DB_PORT")
    cloudsql_instance = cfg(
        "cloudSqlInstance", "finwhiz-ac215:us-central1:finwhiz-cloud-sql"
    )
    agent_url = cfg("agentUrl", "http://agent:8010", env_var="AGENT_URL")
    llm_url = cfg("llmUrl", "http://llm:8001", env_var="LLM_URL")
    supabase_url = cfg("supabaseUrl", "", env_var="SUPABASE_URL")
    supabase_key = cfg_secret("supabaseKey", env_var="SUPABASE_KEY")

    vertex_credentials_path = cfg(
        "vertexCredentials",
        "/app/secrets/service-account-key.json",
        env_var="VERTEXAI_CREDENTIALS",
    )
    vertex_credentials_json = cfg_secret("vertexCredentialsJson")
    db_password = cfg_secret("dbPassword", env_var="DB_PASS")

    shared_secret_name = None
    shared_secret_volume = None
    shared_secret_mount = None
    shared_secret_data = {}
    secret_file_map = {
        "service-account-key.json": secrets_dir / "service-account-key.json",
        "sql_password.txt": secrets_dir / "sql_password.txt",
        "proxy-key.json": secrets_dir / "proxy-key.json",
        "vertexai-service-account.json": secrets_dir / "vertexai-service-account.json",
    }
    for key, path in secret_file_map.items():
        if path.exists():
            shared_secret_data[key] = pulumi.Output.secret(path.read_text())

    if shared_secret_data:
        shared_secret_name = f"{app_name}-shared-secrets"
        k8s.core.v1.Secret(
            shared_secret_name,
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=shared_secret_name, namespace=namespace.metadata.name
            ),
            string_data=shared_secret_data,
            opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
        )
        shared_secret_volume = k8s.core.v1.VolumeArgs(
            name="shared-secrets",
            secret=k8s.core.v1.SecretVolumeSourceArgs(
                secret_name=shared_secret_name,
            ),
        )
        shared_secret_mount = k8s.core.v1.VolumeMountArgs(
            name="shared-secrets",
            mount_path="/app/secrets",
            read_only=True,
        )

    vertex_secret_name = None
    if vertex_credentials_json:
        vertex_secret_name = f"{app_name}-vertex-credentials"
        k8s.core.v1.Secret(
            vertex_secret_name,
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=vertex_secret_name, namespace=namespace.metadata.name
            ),
            string_data={"service-account-key.json": vertex_credentials_json},
            opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
        )

    # Frontend Deployment
    frontend_deployment = k8s.apps.v1.Deployment(
        "frontend",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="frontend", namespace=namespace.metadata.name
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            selector=k8s.meta.v1.LabelSelectorArgs(match_labels={"run": "frontend"}),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(labels={"run": "frontend"}),
                spec=k8s.core.v1.PodSpecArgs(
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name="frontend",
                            image=frontend_image,
                            image_pull_policy="IfNotPresent",
                            env=[
                                k8s.core.v1.EnvVarArgs(name="DOCKER_ENV", value="true")
                            ],
                            ports=[
                                k8s.core.v1.ContainerPortArgs(
                                    container_port=80, protocol="TCP"
                                )
                            ],
                        )
                    ]
                ),
            ),
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
    )

    frontend_service = k8s.core.v1.Service(
        "frontend-service",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="frontend", namespace=namespace.metadata.name
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            type="ClusterIP",
            selector={"run": "frontend"},
            ports=[
                k8s.core.v1.ServicePortArgs(
                    port=80, target_port=80, protocol="TCP"
                )
            ],
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider, depends_on=[frontend_deployment]
        ),
    )

    # Cloud SQL proxy
    proxy_labels = {"run": "cloudsql-proxy"}
    cloudsql_proxy = k8s.apps.v1.Deployment(
        "cloudsql-proxy",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="cloudsql-proxy", namespace=namespace.metadata.name
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            selector=k8s.meta.v1.LabelSelectorArgs(match_labels=proxy_labels),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(labels=proxy_labels),
                spec=k8s.core.v1.PodSpecArgs(
                    service_account_name=ksa_name,
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name="cloudsql-proxy",
                            image="gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.11.3",
                            args=[
                                "--structured-logs",
                                "--auto-iam-authn",
                                "--address=0.0.0.0",
                                f"--port={db_port}",
                                cloudsql_instance,
                            ],
                            ports=[
                                k8s.core.v1.ContainerPortArgs(
                                    container_port=int(db_port), protocol="TCP"
                                )
                            ],
                            resources=k8s.core.v1.ResourceRequirementsArgs(
                                requests={"cpu": "50m", "memory": "128Mi"},
                                limits={"cpu": "200m", "memory": "256Mi"},
                            ),
                        )
                    ],
                ),
            ),
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
    )

    k8s.core.v1.Service(
        "cloudsql-proxy-service",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="cloudsql-proxy", namespace=namespace.metadata.name
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            type="ClusterIP",
            selector=proxy_labels,
            ports=[
                k8s.core.v1.ServicePortArgs(
                    port=int(db_port), target_port=int(db_port), protocol="TCP"
                )
            ],
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider, depends_on=[cloudsql_proxy]
        ),
    )

    # LLM Deployment
    llm_labels = {"run": "llm"}
    llm_volumes = []
    llm_volume_mounts = []
    if vertex_secret_name and not shared_secret_volume:
        vertex_dir, vertex_file = os.path.split(vertex_credentials_path)
        if not vertex_dir:
            vertex_dir = "/app"
        if not vertex_file:
            vertex_file = "service-account-key.json"
        llm_volumes.append(
            k8s.core.v1.VolumeArgs(
                name="vertex-credentials",
                secret=k8s.core.v1.SecretVolumeSourceArgs(
                    secret_name=vertex_secret_name,
                    items=[
                        k8s.core.v1.KeyToPathArgs(key="service-account-key.json", path=vertex_file)
                    ],
                ),
            )
        )
        llm_volume_mounts.append(
            k8s.core.v1.VolumeMountArgs(
                name="vertex-credentials",
                mount_path=vertex_dir,
                read_only=True,
            )
        )
    if shared_secret_volume:
        llm_volumes.append(shared_secret_volume)
        llm_volume_mounts.append(shared_secret_mount)

    llm_env = [
        k8s.core.v1.EnvVarArgs(name="PYTHONPATH", value="/app:/app/src"),
        k8s.core.v1.EnvVarArgs(name="GCP_PROJECT", value=project),
        k8s.core.v1.EnvVarArgs(name="GCS_BUCKET", value=gcs_bucket),
        k8s.core.v1.EnvVarArgs(name="GCS_PREFIX", value=gcs_prefix),
        k8s.core.v1.EnvVarArgs(name="VERTEXAI_CREDENTIALS", value=vertex_credentials_path),
        k8s.core.v1.EnvVarArgs(name="BUCKET_CREDENTIALS", value=vertex_credentials_path),
    ]
    if shared_secret_mount:
        llm_env.append(
            k8s.core.v1.EnvVarArgs(
                name="GOOGLE_APPLICATION_CREDENTIALS",
                value="/app/secrets/service-account-key.json",
            )
        )

    llm_deployment = k8s.apps.v1.Deployment(
        "llm",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="llm", namespace=namespace.metadata.name
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            selector=k8s.meta.v1.LabelSelectorArgs(match_labels=llm_labels),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(labels=llm_labels),
                spec=k8s.core.v1.PodSpecArgs(
                    service_account_name=ksa_name,
                    volumes=llm_volumes if llm_volumes else None,
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name="llm",
                            image=llm_image,
                            image_pull_policy="IfNotPresent",
                            ports=[
                                k8s.core.v1.ContainerPortArgs(
                                    container_port=8001, protocol="TCP"
                                )
                            ],
                            env=llm_env,
                            resources=k8s.core.v1.ResourceRequirementsArgs(
                                requests={"cpu": "1", "memory": "8Gi"},
                                limits={"cpu": "2", "memory": "12Gi"},
                            ),
                            volume_mounts=(
                                llm_volume_mounts if llm_volume_mounts else None
                            ),
                        )
                    ],
                ),
            ),
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
    )

    llm_service = k8s.core.v1.Service(
        "llm-service",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="llm", namespace=namespace.metadata.name
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            selector=llm_labels,
            ports=[
                k8s.core.v1.ServicePortArgs(
                    port=8001, target_port=8001, protocol="TCP"
                )
            ],
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[llm_deployment]),
    )

    # Agent deployment/service
    agent_labels = {"run": "agent"}

    def agent_env():
        env = [
            k8s.core.v1.EnvVarArgs(name="PYTHONPATH", value="/app:/app/src"),
            k8s.core.v1.EnvVarArgs(name="DATABASE_URL", value=database_url),
            k8s.core.v1.EnvVarArgs(name="USER_UPLOAD_BUCKET", value=user_upload_bucket),
            k8s.core.v1.EnvVarArgs(name="GCS_BUCKET", value=gcs_bucket),
            k8s.core.v1.EnvVarArgs(name="GCS_PREFIX", value=gcs_prefix),
            # Extraction uses VertexAI; point to the same credentials file as the LLM
            k8s.core.v1.EnvVarArgs(name="VERTEXAI_CREDENTIALS", value=vertex_credentials_path),
            k8s.core.v1.EnvVarArgs(name="BUCKET_CREDENTIALS", value=vertex_credentials_path),
            k8s.core.v1.EnvVarArgs(name="GCP_PROJECT", value=project),
            k8s.core.v1.EnvVarArgs(name="AGENT_URL", value=agent_url),
            k8s.core.v1.EnvVarArgs(name="LLM_URL", value=llm_url),
            k8s.core.v1.EnvVarArgs(name="DB_USER", value=db_user),
            k8s.core.v1.EnvVarArgs(name="DB_NAME", value=db_name),
            k8s.core.v1.EnvVarArgs(name="DB_HOST", value=db_host),
            k8s.core.v1.EnvVarArgs(name="DB_PORT", value=db_port),
            k8s.core.v1.EnvVarArgs(name="DB_PASS", value="AC215-finwhiz"),
            k8s.core.v1.EnvVarArgs(name="SUPABASE_URL", value=supabase_url),
            k8s.core.v1.EnvVarArgs(name="SUPABASE_KEY", value=supabase_key),
        ]
        if shared_secret_mount:
            env.append(
                k8s.core.v1.EnvVarArgs(
                    name="GOOGLE_APPLICATION_CREDENTIALS",
                    value="/app/secrets/service-account-key.json",
                )
            )
        return env

    agent_deployment = k8s.apps.v1.Deployment(
        "agent",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="agent", namespace=namespace.metadata.name
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            selector=k8s.meta.v1.LabelSelectorArgs(match_labels=agent_labels),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(labels=agent_labels),
                spec=k8s.core.v1.PodSpecArgs(
                    service_account_name=ksa_name,
                    volumes=[shared_secret_volume]
                    if shared_secret_volume
                    else None,
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name="agent",
                            image=agent_image,
                            image_pull_policy="IfNotPresent",
                            working_dir="/app",
                            ports=[
                                k8s.core.v1.ContainerPortArgs(
                                    container_port=8010, protocol="TCP"
                                )
                            ],
                            env=agent_env(),
                            volume_mounts=[shared_secret_mount]
                            if shared_secret_mount
                            else None,
                        )
                    ],
                ),
            ),
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider, depends_on=[llm_service, namespace]
        ),
    )

    agent_service = k8s.core.v1.Service(
        "agent-service",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="agent", namespace=namespace.metadata.name
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            selector=agent_labels,
            ports=[
                k8s.core.v1.ServicePortArgs(
                    port=8010, target_port=8010, protocol="TCP"
                )
            ],
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[agent_deployment], delete_before_replace=False),
    )

    return frontend_service, agent_service
