import os
import sys
import subprocess

# Ensure the virtualenv's Scripts/bin directory is in PATH for all test subprocesses
venv_bin = os.path.dirname(sys.executable)
if venv_bin not in os.environ.get("PATH", "").split(os.pathsep):
    os.environ["PATH"] = f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}"

# Monkeypatch subprocess to default to UTF-8 with errors='replace' on Windows when text=True
if os.name == "nt":
    _original_run = subprocess.run
    _original_Popen = subprocess.Popen

    def _patched_run(*args, **kwargs):
        if kwargs.get('text') or kwargs.get('universal_newlines'):
            if 'encoding' not in kwargs:
                kwargs['encoding'] = 'utf-8'
            if 'errors' not in kwargs:
                kwargs['errors'] = 'replace'
        return _original_run(*args, **kwargs)

    class _PatchedPopen(_original_Popen):
        def __init__(self, *args, **kwargs):
            if kwargs.get('text') or kwargs.get('universal_newlines'):
                if 'encoding' not in kwargs:
                    kwargs['encoding'] = 'utf-8'
                if 'errors' not in kwargs:
                    kwargs['errors'] = 'replace'
            super().__init__(*args, **kwargs)

    subprocess.run = _patched_run
    subprocess.Popen = _PatchedPopen
