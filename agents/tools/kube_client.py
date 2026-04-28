import subprocess
import tempfile
from typing import Optional


class KubeClient:
    def __init__(self, kubeconfig_content: Optional[str] = None):
        self._kubeconfig_content = kubeconfig_content
        self._tmpfile: Optional[str] = None

    def _write_config(self):
        if self._kubeconfig_content:
            self._tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
            self._tmpfile.write(self._kubeconfig_content.encode())
            self._tmpfile.flush()
            self._tmpfile.close()

    def _cleanup(self):
        if self._tmpfile:
            import os
            os.unlink(self._tmpfile.name)
            self._tmpfile = None

    def _env(self) -> dict:
        import os
        env = os.environ.copy()
        if self._tmpfile:
            env["KUBECONFIG"] = self._tmpfile.name
        return env

    def kubectl(self, args: str, timeout: int = 30) -> dict:
        self._write_config()
        try:
            result = subprocess.run(
                f"kubectl {args}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._env(),
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        finally:
            self._cleanup()

    def helm_install(self, release: str, chart: str, namespace: str = "default", values: Optional[str] = None) -> dict:
        self._write_config()
        cmd = f"helm install {release} {chart} -n {namespace}"
        if values:
            cmd += f" -f {values}"
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=120, env=self._env()
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        finally:
            self._cleanup()
