#!/bin/bash


if [ $(id -u) != 0 ] ; then
  echo "Les droits Superuser (root) sont nécessaires pour installer media_docker_linux"
  echo "Lancez 'sudo $0' pour obtenir les droits Superuser."
  exit 1
fi

is_valid_python3_version() {
    [[ $1 =~ ^python3\.[0-9]+$ ]]
}
PYTHON_VERSIONS=($(compgen -c python3. | sort -Vr))
PYTHON_COMMAND=""
for version in "${PYTHON_VERSIONS[@]}"
do
    if is_valid_python3_version "$version" && command -v $version &> /dev/null
    then
        ver_number=${version#python3.}
        if (( ver_number >= 6 ))
        then
            PYTHON_COMMAND=$version
            break
        fi
    fi
done
if [[ -z $PYTHON_COMMAND ]]
then
    echo "Une version 3.6 minimum de Python est nécessaire."
    echo "Merci d'installer une version de Python supérieur ou égale à 3.6 puis de relancer le programme."
    exit 1
else
    echo "Utilisation de $PYTHON_COMMAND (version $($PYTHON_COMMAND --version 2>&1 | cut -d' ' -f2))"
fi

echo -e "Installation des librairies nécessaires\n"

step_1_update() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 1 - Update"
  apt update
  echo "Step 1 - Update done"
}

step_2_mainpackage() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 2 - packages"
  apt -y install curl
  apt -y install unzip
  echo "step 2 - packages done"
}

step_3_media_docker_linux_download() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 3 - media_docker_linux download"
  user=${SUDO_USER:-${USER}}
  cd /opt && curl https://github.com/mediaselect/media-docker-linux/archive/refs/tags/v1.0.0.zip -L -o media-docker-linux.zip
  media_free_docker=$(ls /opt | grep media-docker-linux)
  if [ -n "$media_free_docker" ]
  then
    rm -rf /opt/media-docker-linux
  fi
  unzip media-docker-linux.zip
  mv media-docker-linux-1.0.0 media-docker-linux
  rm media-docker-linux.zip
  echo "Step 3 - media_docker_linux download done"
}

step_4_create_media-docker-linux_directories() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 4 - Creating media-docker-linux directories"
  user=${SUDO_USER:-${USER}}
  mkdir -p /etc/media-docker-linux
  echo "User: $user"
  mkdir -p /home/$user/.local/share/media-docker-linux
  mkdir -p /home/$user/.config/media-docker-linux
  mkdir -p /var/log/media-docker-linux
  chown $user:$user /home/$user/.local/share/media-docker-linux
  chown $user:$user /home/$user/.config/media-docker-linux
  chown $user:$user /var/log/media-docker-linux
  if [ ! -f /home/$user/.config/media-docker-linux/config.ini ]; then
    sudo -u $user cp /opt/media-docker-linux/config.ini /home/$user/.config/media-docker-linux/config.ini
  fi
  echo "Step 6 - media-docker-linux directories created"
}


STEP=0

case ${STEP} in
  0)
  echo "Starting installation ..."
  step_1_update
  step_2_mainpackage
  step_3_media_docker_linux_download
  step_4_create_media-docker-linux_directories
  ;;
esac
