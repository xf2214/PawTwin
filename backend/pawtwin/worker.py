"""Background analysis worker: lease claiming, renewal and admission control.

Day-3 (ruling 7) drains the queue CONCURRENTLY through a bounded thread pool sized
to ``max_concurrent_global``. Admission is acquired before a run is submitted and
released when its analysis finishes, so the documented ceilings (one analysis per
login session, two site-wide) now have a REAL production trigger path -- this
closes the Day-2 nit that a sequential drain never exercised them. Scope is still a
SINGLE PROCESS: the ceilings are in-process, and a cross-REPLICA ceiling needs
database-level counting (Day-4/T7). The Day-2 CAS / claim-whitelist / lease
primitives are what keep concurrent analysis safe; they are unchanged.

The worker only ever starts inside the application lifespan, so ``create_app``
stays side-effect free and the offline contract export never spawns a thread.
"""

from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from pawtwin.config import Settings
from pawtwin.repository import Repository
from pawtwin.workflow import Workflow

logger = logging.getLogger(__name__)

# Short enough that the queue wait stays well inside the frontend polling budget,
# long enough to keep an idle process quiet. ``notify`` removes the wait entirely
# right after an enqueue.
POLL_INTERVAL_SECONDS = 0.5


def _now() -> datetime:
    return datetime.now(UTC)


class AdmissionControl:
    """In-process concurrency ceiling (one per session, two site-wide)."""

    def __init__(self, per_session: int, global_limit: int) -> None:
        self._per_session = max(1, per_session)
        self._global_limit = max(1, global_limit)
        self._lock = threading.Lock()
        self._by_owner: dict[str, int] = {}

    @property
    def active(self) -> int:
        with self._lock:
            return sum(self._by_owner.values())

    def try_acquire(self, owner_id: str) -> bool:
        with self._lock:
            current = self._by_owner.get(owner_id, 0)
            if current >= self._per_session or self.active_unlocked() >= self._global_limit:
                return False
            self._by_owner[owner_id] = current + 1
            return True

    def release(self, owner_id: str) -> None:
        with self._lock:
            current = self._by_owner.get(owner_id, 0)
            if current <= 1:
                self._by_owner.pop(owner_id, None)
            else:
                self._by_owner[owner_id] = current - 1

    def active_unlocked(self) -> int:
        return sum(self._by_owner.values())


class LeaseRenewer:
    """Renews a lease while a long analysis runs.

    ``claim_run`` cannot renew: its predicate rejects a live lease for everyone,
    including the holder. Renewal therefore needs its own statement, run on a timer
    for the duration of one analysis.
    """

    def __init__(
        self,
        repo: Repository,
        run_id: uuid.UUID,
        worker_id: str,
        *,
        lease_seconds: int,
        renew_seconds: int,
    ) -> None:
        self._repo = repo
        self._run_id = run_id
        self._worker_id = worker_id
        self._lease_seconds = lease_seconds
        self._renew_seconds = renew_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.renewals = 0

    def __enter__(self) -> LeaseRenewer:
        self._thread = threading.Thread(
            target=self._loop, name=f"pawtwin-lease-{self._run_id}", daemon=True
        )
        self._thread.start()
        return self

    def _loop(self) -> None:
        while not self._stop.wait(self._renew_seconds):
            until = _now() + timedelta(seconds=self._lease_seconds)
            if self._repo.renew_lease(self._run_id, self._worker_id, until):
                self.renewals += 1

    def __exit__(self, *_exc: object) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=1.0)


class AnalysisWorker:
    """Drains claimable runs CONCURRENTLY. Start/stop it from the lifespan only.

    Day-3 (ruling 7): a bounded thread pool sized to ``max_concurrent_global``
    replaces the Day-2 sequential drain. Admission is acquired BEFORE a run is
    submitted and released when its analysis finishes, so the per-session/site-wide
    ceilings gate real work (Day-2 nit#6): one owner who queues two events is
    serialised at a single analysis, and two owners run two analyses at once but
    never a third. Each in-flight run gets a UNIQUE worker id so lease ownership
    stays unambiguous under parallelism.
    """

    def __init__(
        self,
        repo: Repository,
        workflow: Workflow,
        settings: Settings,
        *,
        worker_id: str | None = None,
        poll_interval: float = POLL_INTERVAL_SECONDS,
    ) -> None:
        self._repo = repo
        self._workflow = workflow
        self._settings = settings
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self._poll_interval = poll_interval
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._pool: ThreadPoolExecutor | None = None
        self._inflight: dict[Future, str] = {}
        self._inflight_lock = threading.Lock()
        self._max_concurrent = max(1, settings.max_concurrent_global)
        self.admission = AdmissionControl(
            settings.max_concurrent_per_session, settings.max_concurrent_global
        )
        self._count_lock = threading.Lock()
        self.processed = 0
        # Observability: how many analyses ran at once (high-water mark). Proves
        # the ceilings are really exercised rather than merely present.
        self._active = 0
        self.peak_concurrency = 0

    @property
    def running(self) -> bool:
        return self._thread is not None

    def notify(self) -> None:
        """Wake the loop right after an enqueue so the queue wait stays under 2s."""

        self._wake.set()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._ensure_pool()
        self._thread = threading.Thread(
            target=self._run, name="pawtwin-worker-scan", daemon=True
        )
        self._thread.start()

    def _ensure_pool(self) -> ThreadPoolExecutor:
        # Constructing a ThreadPoolExecutor spawns no thread until a task is
        # submitted, so this keeps ``create_app`` side-effect free.
        if self._pool is None:
            self._pool = ThreadPoolExecutor(
                max_workers=self._max_concurrent, thread_name_prefix="pawtwin-worker"
            )
        return self._pool

    def stop(self, timeout: float = 2.0) -> None:
        """Stop the scan loop, then release the pool WITHOUT blocking process exit.

        Mirrors :meth:`pawtwin.workflow.AnalysisGuard.shutdown`: a runaway analysis
        may never hang shutdown. Queued (not-yet-started) tasks are cancelled; a
        running task is a daemon thread whose repository writes are lease-guarded,
        so abandoning it cannot corrupt a settled run.
        """

        self._stop.set()
        self._wake.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=timeout)
        pool, self._pool = self._pool, None
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                submitted = self.drain_once()
            except Exception:  # noqa: BLE001 - the loop must never die silently
                logger.exception("worker pass failed")
                submitted = 0
            if submitted == 0:
                self._wake.wait(timeout=self._poll_interval)
                self._wake.clear()

    def drain_once(self) -> int:
        """One scan pass: submit admissible claimable runs to the pool.

        Returns how many runs were SUBMITTED (not completed). Admission is acquired
        here, before the claim, so a run that cannot be admitted stays QUEUED rather
        than being dropped or forced -- and is retried by a later pass.
        """

        pool = self._ensure_pool()
        submitted = 0
        for record in self._repo.list_claimable_runs(
            limit=max(1, self._settings.max_concurrent_global)
        ):
            if self._stop.is_set():
                break
            if not self.admission.try_acquire(record.owner_id):
                # Ceiling reached: leave it queued rather than dropping or forcing it.
                continue
            task_worker_id = f"{self.worker_id}-{record.run_id.hex[:8]}"
            try:
                future = pool.submit(
                    self._process, record.run_id, record.owner_id, task_worker_id
                )
            except RuntimeError:
                # The pool was shut down mid-scan (stop() raced this pass): give back
                # the slot reserved above, since no task will ever release it.
                self.admission.release(record.owner_id)
                break
            with self._inflight_lock:
                self._inflight[future] = record.owner_id
            future.add_done_callback(self._on_done)
            submitted += 1
        return submitted

    def _on_done(self, future: Future) -> None:  # type: ignore[type-arg]
        with self._inflight_lock:
            owner_id = self._inflight.pop(future, None)
        # A task cancelled before it ran (shutdown) never reached its finally, so
        # hand back the admission slot it reserved.
        if owner_id is not None and future.cancelled():
            self.admission.release(owner_id)

    def _process(self, run_id: uuid.UUID, owner_id: str, task_worker_id: str) -> None:
        with self._count_lock:
            self._active += 1
            if self._active > self.peak_concurrency:
                self.peak_concurrency = self._active
        try:
            with LeaseRenewer(
                self._repo,
                run_id,
                task_worker_id,
                lease_seconds=self._settings.lease_seconds,
                renew_seconds=self._settings.lease_renew_seconds,
            ):
                result = self._workflow.analyze_run(run_id, task_worker_id)
            if result is not None:
                with self._count_lock:
                    self.processed += 1
        except Exception:  # noqa: BLE001 - one bad task must not kill the pool
            logger.exception("analysis task failed")
        finally:
            with self._count_lock:
                self._active -= 1
            self.admission.release(owner_id)
