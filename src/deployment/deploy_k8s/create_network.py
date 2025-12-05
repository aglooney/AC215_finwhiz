import pulumi_gcp as gcp


def create_network(region, app_name):
    network_name = f"{app_name}-network"
    subnet_name = f"{app_name}-subnet"

    network = gcp.compute.Network(
        network_name,
        name=network_name,
        auto_create_subnetworks=False,
        routing_mode="REGIONAL",
        description=f"{app_name} VPC for private GKE",
    )

    subnet = gcp.compute.Subnetwork(
        subnet_name,
        name=subnet_name,
        ip_cidr_range="10.10.0.0/16",
        region=region,
        network=network.id,
        private_ip_google_access=True,
        description=f"{app_name} subnet",
    )

    router = gcp.compute.Router(
        f"{app_name}-router",
        name=f"{app_name}-router",
        network=network.id,
        region=region,
    )

    nat = gcp.compute.RouterNat(
        f"{app_name}-nat",
        name=f"{app_name}-nat",
        router=router.name,
        region=region,
        nat_ip_allocate_option="AUTO_ONLY",
        source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",
        log_config=gcp.compute.RouterNatLogConfigArgs(enable=True, filter="ERRORS_ONLY"),
    )

    return network, subnet, router, nat
