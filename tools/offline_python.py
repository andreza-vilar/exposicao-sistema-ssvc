#!/usr/bin/env python3
"""Launcher local: usar .venv/bin/python -I -S -B tools/offline_python.py SCRIPT.

Ambiente externo deve ser limpo com env -i. Não lê configurações de usuário,
não processa .pth e não faz descoberta de SDKs. Audit hooks são defesa adicional,
não uma sandbox de SO nem uma barreira contra código nativo malicioso.
"""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = tuple({Path(sys.base_prefix).resolve(), Path(sys.base_exec_prefix).resolve(),
                 Path('/System/Library'), Path('/usr/lib')})


def inside(path, root):
    return path == root or root in path.parents


def checked_path(value, write=False):
    if isinstance(value, int):  # stdin/stdout/stderr and already-open descriptors
        return
    path = Path(os.fsdecode(value)).resolve()
    if inside(path, ROOT):
        return
    if not write and any(inside(path, root) for root in RUNTIME):
        return
    raise PermissionError('offline guard: acesso fora do projeto/runtime recusado')


def audit(event, args):
    if event.startswith(('socket.', 'subprocess.', 'ctypes.')) or event in {
        'os.system', 'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.exec',
        'os.spawn', 'pty.spawn',
    }:
        raise PermissionError('offline guard: rede/subprocesso/código nativo recusado')
    if event == 'open':
        path, mode, flags = args
        write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        checked_path(path, write)
    elif event in {'os.listdir', 'os.scandir', 'os.chdir'}:
        checked_path(args[0] if args[0] is not None else ROOT)
    elif event in {'os.remove', 'os.rmdir', 'os.mkdir', 'os.chmod', 'os.utime'}:
        checked_path(args[0], write=True)
    elif event in {'os.rename', 'os.link', 'os.symlink'}:
        checked_path(args[0], write=True)
        checked_path(args[1], write=True)


def main():
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise SystemExit('Use .venv/bin/python -I -S -B tools/offline_python.py SCRIPT')
    if len(sys.argv) < 2:
        raise SystemExit('Informe um script local do projeto')
    target = Path(sys.argv[1]).resolve()
    if not inside(target, ROOT) or not target.is_file():
        raise SystemExit('Script deve ser arquivo dentro do projeto')
    # Importar somente o pacote já instalado no venv, sem site/.pth/usercustomize.
    packages = ROOT / '.venv' / 'lib' / ('python%d.%d' % sys.version_info[:2]) / 'site-packages'
    sys.path[:0] = [str(ROOT), str(packages)]
    os.chdir(ROOT)
    sys.addaudithook(audit)
    import runpy
    sys.argv = [str(target)] + sys.argv[2:]
    runpy.run_path(str(target), run_name='__main__')


if __name__ == '__main__':
    main()
