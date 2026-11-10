"""Cancellable process-group helpers shared by harness adapters."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class CancellableRun:
    stdout: str
    stderr: str
    returncode: int
    cancelled: bool
    timed_out: bool


def kill_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGKILL)


def run_cancellable_subprocess(
    argv: list[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    timeout: int,
    cancel_event: threading.Event,
) -> CancellableRun:
    """Run argv in a new session; kill the process group on cancel or timeout."""
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    cancelled = threading.Event()
    watcher_done = threading.Event()

    def watch_cancellation() -> None:
        while not watcher_done.is_set() and process.poll() is None:
            if cancel_event.wait(0.05):
                cancelled.set()
                kill_process_group(process)
                return

    watcher = threading.Thread(target=watch_cancellation)
    watcher.start()
    timed_out = False
    stdout = ""
    stderr = ""
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_process_group(process)
        process.wait(timeout=5)
    watcher_done.set()
    watcher.join(timeout=1)
    returncode = process.returncode if process.returncode is not None else -1
    return CancellableRun(
        stdout=stdout or "",
        stderr=stderr or "",
        returncode=returncode,
        cancelled=cancelled.is_set(),
        timed_out=timed_out,
    )
