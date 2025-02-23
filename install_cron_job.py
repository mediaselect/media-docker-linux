import os
import subprocess
import configparser
from datetime import datetime

user_home = os.path.expanduser("~")
config_path = f"{user_home}/.config/media-docker-linux/config.ini"
config = configparser.ConfigParser()
config.read(config_path)

def backup_crontab():
    # Function to back up the existing crontab
    backup_filename = f"/tmp/crontab_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
    try:
        with open(backup_filename, "w") as backup_file:
            subprocess.run(["crontab", "-l"], stdout=backup_file, check=True)
        print(f"Crontab existant sauvegardé dans : {backup_filename}")
    except subprocess.CalledProcessError:
        print("Aucun crontab existant à sauvegarder.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du crontab : {e}")

def add_cron_job():
    # Function to add the new cron job
    user = os.getenv('USER')
    cron_job_time = "*/5 * * * *"
    cron_job_command = f"export USER='{user}' && bash /opt/media-docker-linux/cron_manage_container.sh >> /var/log/media-docker-linux/manage_container.log 2>&1"
    cron_job = f"{cron_job_time} {cron_job_command}\n"

    backup_crontab()

    try:
        current_crontab = subprocess.check_output(["crontab", "-l"], text=True)
    except subprocess.CalledProcessError:
        current_crontab = ""

    # Check if the exact cron job command already exists
    if any(cron_job_command in line for line in current_crontab.splitlines()):
        print("\nLa tâche cron existe déjà. Aucun changement réalisé.")
        return

    new_crontab = current_crontab + cron_job
    with subprocess.Popen(['crontab'], stdin=subprocess.PIPE, text=True) as proc:
        proc.communicate(new_crontab)

    print("\nLa tâche Cron job a été ajoutée!")

def main():
    # answers = ["oui", "non"]
    # docker_desktop = "no_se"
    # while docker_desktop.lower() not in answers:
    #     docker_desktop = input(
    #         "\nUtilisez vous Docker Desktop (application graphique GUI) pour "
    #         "démarrer votre conteneur Docker? (répondre par oui ou non): ").strip().lower()
    # if docker_desktop == "oui":
    #     config.set('Docker', 'docker_desktop', 'true')
    # else:
    #     config.set('Docker', 'docker_desktop', 'false')

    # with open(config_path, 'w') as configfile:
    #     config.write(configfile)

    user = os.getenv('USER')
    print(f"\nConfiguration de la tâche cron pour contrôler "
          "le démarrage et l'arrêt du conteneur Docker "
          "media-docker-linux de Media-select pour "
          f"l'utilisateur : {user}\n")

    confirmation = input("Cela ajoutera une nouvelle tâche cron à votre crontab. Continuer ? (o/n): ").strip().lower()

    if confirmation in ['o', 'oui']:
        add_cron_job()
    else:
        print("\nConfiguration de la tâche cron annulée.")

if __name__ == "__main__":
    main()
