import io
from typing import Optional

import paramiko


class SSHClientManager:
    def __init__(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        key_pem: Optional[str] = None,
        port: int = 22,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.key_pem = key_pem
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None

    def __enter__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
            "timeout": 30,
            "banner_timeout": 30,
        }

        if self.key_pem:
            key_file = io.StringIO(self.key_pem)
            private_key = paramiko.RSAKey.from_private_key(key_file)
            connect_kwargs["pkey"] = private_key
        elif self.password:
            connect_kwargs["password"] = self.password
        else:
            raise ValueError("Se requiere key_pem o password para autenticacion SSH")

        self.client.connect(**connect_kwargs)
        return self

    def __exit__(self, *args):
        if self.client:
            self.client.close()

    def execute(self, command: str, timeout: int = 60) -> dict:
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return {
            "stdout": stdout.read().decode("utf-8", errors="replace"),
            "stderr": stderr.read().decode("utf-8", errors="replace"),
            "exit_code": exit_code,
        }

    def transfer_file(self, local_path: str, remote_path: str):
        with self.client.open_sftp() as sftp:
            sftp.put(local_path, remote_path)
