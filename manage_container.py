import os
import subprocess
import logging
import configparser
from logging.handlers import RotatingFileHandler
from datetime import datetime

user_home = os.path.expanduser("~")
config = configparser.ConfigParser()
config.read(f"{user_home}/.config/media-docker-linux/config.ini")

container_name = config['Docker']['container_name']
docker_desktop = config['Docker'].getboolean('docker_desktop')

LOG_FILE = f"/var/log/media-docker-linux/manage_container.log"
INFO_PROGS_FILE = f"/home/{os.getenv('USER')}/.local/share/media-free-docker/info_progs.json"
INFO_PROGS_LAST_FILE = f"/home/{os.getenv('USER')}/.local/share/media-free-docker/info_progs_last.json"
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

home_dir = os.path.expanduser("~")

def is_docker_responsive(socket):
    try:
        output = subprocess.run(
            ["docker", "--host", socket, "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2
        )
        return output.returncode == 0
    except Exception:
        return False

def get_docker_socket():

    docker_sockets = [
        "unix:///var/run/docker.sock",                  # Docker Engine (Linux)
        f"unix://{home_dir}/.docker/desktop/docker.sock",  # Docker Desktop (user-specific)
        "unix:///run/docker.sock"                       # Alternative Docker Engine path
    ]
    for socket in docker_sockets:
        socket_path = socket.replace("unix://", "")
        if os.path.exists(socket_path) and is_docker_responsive(socket):
            return socket

    return None

def setup_logger():
    logger = logging.getLogger("ManageContainer")
    logger.setLevel(logging.DEBUG)

    handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_FILE_SIZE, backupCount=BACKUP_COUNT)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def get_file_modification_time(file_path):
    try:
        mod_time = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mod_time)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None

def is_container_docker_desktop_running(container_name):

    try:
        env["DOCKER_HOST"] = f"unix://{home_dir}/.docker/desktop/docker.sock"
        logger.info(f'DOCKER_HOST={env["DOCKER_HOST"]}')
        output = subprocess.check_output(["docker", "ps", "-q", "-f", f"name={container_name}"], env=env)
        if output.strip():
            return True
    except FileNotFoundError:
        logger.error("Docker is not installed or not found in PATH.")
    except PermissionError:
        logger.error("Permission denied: Cannot access Docker socket. Are you in the 'docker' group?")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking container status: {e.output.decode().strip()}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")

    return False

def is_container_docker_engine_running(container_name):

    try:
        env["DOCKER_HOST"] = "unix:///var/run/docker.sock"
        logger.info(f'DOCKER_HOST={env["DOCKER_HOST"]}')
        output = subprocess.check_output(["docker", "ps", "-q", "-f", f"name={container_name}"], env=env)
        if output.strip():
            return True
    except FileNotFoundError:
        logger.error("Docker is not installed or not found in PATH.")
    except PermissionError:
        logger.error("Permission denied: Cannot access Docker socket. Are you in the 'docker' group?")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking container status: {e.output.decode().strip()}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")

    return False

def start_container_docker_desktop(container_name):
    try:
        env["DOCKER_HOST"] = f"unix://{home_dir}/.docker/desktop/docker.sock"
        subprocess.run(["docker", "start", container_name], env=env, check=True)
        logger.info(f"Started Docker Desktop container '{container_name}'.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Docker Desktop container: {e}")

def start_container_docker_engine(container_name):
    try:
        env["DOCKER_HOST"] = "unix:///var/run/docker.sock"
        subprocess.run(["docker", "start", container_name], env=env, check=True)
        logger.info(f"Started Docker Engine container '{container_name}'.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Docker Engine container: {e}")


def stop_container_docker_desktop(container_name):
    try:
        env["DOCKER_HOST"] = f"unix://{home_dir}/.docker/desktop/docker.sock"
        subprocess.run(["docker", "stop", container_name], env=env, check=True)
        logger.info(f"Stopped Docker Desktop container '{container_name}'.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to stop Docker Desktop container: {e}")

def stop_container_docker_engine(container_name):
    try:
        env["DOCKER_HOST"] = "unix:///var/run/docker.sock"
        subprocess.run(["docker", "stop", container_name], env=env, check=True)
        logger.info(f"Stopped Docker Engine container '{container_name}'.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to stop Docker Engine container: {e}")

def manage_container():
    current_time = datetime.now()
    info_progs_mod_time = get_file_modification_time(INFO_PROGS_FILE)
    info_progs_last_mod_time = get_file_modification_time(INFO_PROGS_LAST_FILE)

    if info_progs_mod_time is None:
        if docker_desktop:
            logger.warning(f"Starting Docker Desktop container '{container_name}' because the file was not found.")
            start_container_docker_desktop(container_name)
            return
        else:
            logger.warning(f"Starting Docker Engine container '{container_name}' because the file was not found.")
            start_container_docker_engine(container_name)
            return

    if info_progs_mod_time.date() < current_time.date():
        if docker_desktop:
            if not is_container_docker_desktop_running(container_name):
                start_container_docker_desktop(container_name)
            else:
                logger.info(f"Container Docker Desktop '{container_name}' is already running.")
        else:
            if not is_container_docker_engine_running(container_name):
                start_container_docker_engine(container_name)
            else:
                logger.info(f"Container Docker Engine '{container_name}' is already running.")
    else:
        should_stop = False

        if info_progs_last_mod_time and info_progs_last_mod_time.date() == current_time.date():
            should_stop = True

        # if should_stop and is_container_docker_desktop_running(container_name):
        #     logger.info(f"Stopping Docker Desktop container '{container_name}' because info_progs_last.json is up-to-date.")
        #     stop_container_docker_desktop(container_name)

        if should_stop and is_container_docker_engine_running(container_name):
            logger.info(f"Stopping Docker Engine container '{container_name}' because info_progs_last.json is up-to-date.")
            stop_container_docker_engine(container_name)


if __name__ == "__main__":
    logger = setup_logger()
    docker_host = get_docker_socket()
    env = os.environ.copy()

    if docker_host:
        env["DOCKER_HOST"] = docker_host

    manage_container()
