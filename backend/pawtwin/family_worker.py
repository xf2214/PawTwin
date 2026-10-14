"""Persistent-cursor reporting, independent of opening the browser."""

import threading

from pawtwin.home_store import now_iso


class FamilyReportWorker:
    def __init__(self, store, interval_seconds=60):
        self.store = store
        self.interval = interval_seconds
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._loop, name="family-reports", daemon=True)
        self.thread.start()

    def _loop(self):
        while not self.stop_event.is_set():
            try:
                self.store.run_due_reports()
                status = "ok:" + now_iso()
            except Exception:
                status = "failed:" + now_iso()
            with self.store.lock, self.store.conn:
                self.store.conn.execute(
                    "INSERT OR REPLACE INTO family_metadata VALUES ('report_worker',?)", (status,)
                )
            self.stop_event.wait(self.interval)

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=20)
