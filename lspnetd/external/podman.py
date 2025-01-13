import json
from lspnetd.common.utils import sudo_call, sudo_call_output, get_tempdir_path
from lspnetd.common.logger import get_logger
from lspnetd.models.container import ContainerBindMountStatus, ContainerStatus


logger = get_logger("podman")


def inspect_podman_container(container_name: str):
    container_list = sudo_call_output(["podman", "ps", "-a", "--format=json"])
    container_list = json.loads(container_list)

    for container_info in container_list:
        if container_name in container_info['Names']:
            container_inspect_result = sudo_call_output(["podman", "container", "inspect", container_info['Id']])
            container_inspect_result = json.loads(container_inspect_result)
            
            mounts: list[ContainerBindMountStatus] = []
            for bind_mount in container_inspect_result[0]["HostConfig"]["Binds"]:
                parts = bind_mount.split(':')
                mounts.append(ContainerBindMountStatus(
                    source=parts[0],
                    target=parts[1],
                    flags=parts[2:].split(',')
                ))
            
            return ContainerStatus(
                id=container_info['Id'],
                bind_mounts=mounts
            )


def shutdown_podman_router(namespace: str):
    container_status = inspect_podman_container(f"{namespace}-router")
    if not container_status:
        return

    logger.info('removing container: {}'.format(container_status.id))
    sudo_call(["podman", "rm", "-f", container_status.id])

    # make sure legacy mount/tmpfiles are cleared
    for mount in container_status.bind_mounts:
        if mount.source.startswith(get_tempdir_path(namespace)):
            logger.info('removing temp directory: {}'.format(mount.source))
            sudo_call(["rm", "-rf", mount.source])


def start_podman_router(namespace: str):
    logger.info('starting router with namespace {}'.format(namespace))
    sudo_call(["podman", "run", "--network", f"ns:/var/run/netns/{namespace}", 
               "--cap-add", "NET_ADMIN", "--cap-add", "CAP_NET_BIND_SERVICE", "--cap-add", "NET_RAW", "--cap-add", "NET_BROADCAST",
               "-v", f"{get_tempdir_path(namespace)}/router:/data:ro", "--name", f"{namespace}-router",
               "-d", "bird-router"])
