from __future__ import annotations

import datetime
import os
from pathlib import Path

import pulumi
import pulumi_docker_build as docker_build
from pulumi import CustomTimeouts

ROOT = Path(__file__).resolve().parents[2]

project = pulumi.Config("gcp").require("project")
location = os.environ["GCP_REGION"]

repository_name = os.getenv("GAR_REPOSITORY", "finwhiz-img")
base_image_name = os.getenv("GAR_IMAGE_NAME", "finwhiz")
registry = f"{location}-docker.pkg.dev/{project}/{repository_name}/{base_image_name}"

timestamp_suffix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")

services = [
    {
        "name": "llm",
        "context": ROOT / "llm",
        "dockerfile": ROOT / "llm" / "Dockerfile",
    },
    {
        "name": "agent",
        "context": ROOT / "agentic_user_data_processing",
        "dockerfile": ROOT / "agentic_user_data_processing" / "Dockerfile",
    },
    {
        "name": "client",
        "context": ROOT / "query_client",
        "dockerfile": ROOT / "query_client" / "Dockerfile",
    },
    {
        "name": "frontend",
        "context": ROOT / "frontend",
        "dockerfile": ROOT / "frontend" / "Dockerfile",
    },
]


def build_service_image(service: dict) -> None:
    service_name = service["name"]
    context_path = str(service["context"])
    dockerfile_path = str(service["dockerfile"])

    tags = [
        pulumi.Output.concat(registry, ":", service_name),
        pulumi.Output.concat(registry, ":", service_name, "-", timestamp_suffix),
    ]

    image = docker_build.Image(
        f"build-{service_name}",
        tags=tags,
        context=docker_build.BuildContextArgs(location=context_path),
        dockerfile={"location": dockerfile_path},
        platforms=[docker_build.Platform.LINUX_AMD64],
        push=True,
        opts=pulumi.ResourceOptions(
            custom_timeouts=CustomTimeouts(create="30m"),
            retain_on_delete=True,
        ),
    )

    pulumi.export(f"finwhiz-{service_name}-ref", image.ref)
    pulumi.export(f"finwhiz-{service_name}-tags", image.tags)


for svc in services:
    build_service_image(svc)
