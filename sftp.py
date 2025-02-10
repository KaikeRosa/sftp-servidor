import os
import paramiko
import time

HOST = "IP"
PORT = "PORTA"
USERNAME = "USUARIO"
PASSWORD = "SENHA"
REMOTE_PATH = "PASTA REMOTA"
LOCAL_PATH = "PASTA LOCAL"

TEMP_FILE_EXTENSIONS = ['.crdownload', '.part', '.temp']

def progress(filename, bytes_sent, total_bytes):
    """porcentagem de envio do arquivo """
    percent = (bytes_sent / total_bytes) * 100
    print(f"Enviando {filename}: {percent:.2f}% completo", end='\r')

def transfer_files(file):
    """ função que transfere o arquivo para o servidor"""

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD)
    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")
        return

    sftp = ssh.open_sftp()

    try:
        local_file = os.path.join(LOCAL_PATH, file)
        remote_file = os.path.join(REMOTE_PATH, file)


        try:
            sftp.stat(remote_file)
            print(f"arquivo {file} já existe no servidor")
            return
        except FileNotFoundError:
            pass


        total_size = os.path.getsize(local_file)


        print(f"iniciando o envio de {file}...")
        sftp.put(local_file, remote_file, callback=lambda bytes_sent, total_size=total_size: progress(file, bytes_sent, total_size))
        print(f"{file} enviado.")


        os.remove(local_file)
        print(f"{file} removido")

    except Exception as e:
        print(f"erro {file}: {e}")

    finally:
        sftp.close()
        ssh.close()

def check_for_temp_files():
    """ verifica se existem arquivos temporários (.part) na pasta """
    files_in_directory = os.listdir(LOCAL_PATH)
    for temp_extension in TEMP_FILE_EXTENSIONS:
        for file in files_in_directory:
            if file.endswith(temp_extension):
                print(f"arquivo temporário encontrado: {file}")
                return True
    return False

def is_file_complete(file_path, check_interval=5, max_wait_time=60):
    """
    verifica se o arquivo está completo
    """
    try:
        initial_size = os.path.getsize(file_path)
        wait_time = 0

        while wait_time < max_wait_time:
            time.sleep(check_interval)
            current_size = os.path.getsize(file_path)
            if current_size == initial_size:
                return True
            initial_size = current_size
            wait_time += check_interval

        print(f"Arquivo {file_path} ainda está baixando após {max_wait_time} segundos.")
        return False
    except FileNotFoundError:
        return False

def monitor_folder():
    print(f"Rodando em: {LOCAL_PATH}")

    while True:

        if check_for_temp_files():
            print("Aguardando o término dos downloads...")


            while check_for_temp_files():
                time.sleep(5)
            print("Todos os downloads concluídos. Transferindo arquivos.")

        files_in_directory = os.listdir(LOCAL_PATH)

        for new_file in files_in_directory:

            if any(new_file.endswith(ext) for ext in TEMP_FILE_EXTENSIONS):
                continue

            file_path = os.path.join(LOCAL_PATH, new_file)

            if os.path.isfile(file_path):

                if is_file_complete(file_path):
                    print(f"o arquivo {new_file} está completo")

                    transfer_files(new_file)
                else:
                    print(f"aguardando {new_file} baixar")

        time.sleep(5)

if __name__ == "__main__":
    monitor_folder()

