"""Local identity and household store, separated from legacy data and device quotas."""

import hashlib
import json
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from pawtwin.growth import build_report, parse, put_report
from pawtwin.home_store import HomeStore, initial_home, new_id, now_iso

SEED_USER = "00000000-0000-4000-8000-000000000001"


def password_hash(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return f"scrypt${salt}${digest.hex()}"


class FamilyStore(HomeStore):
    def __init__(self, path: str):
        self.device_source = None
        super().__init__(path)
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS family_users (
                    id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                    name TEXT NOT NULL, avatar TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS family_households (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, timezone TEXT NOT NULL,
                    created_by TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS family_memberships (
                    household TEXT NOT NULL, user TEXT NOT NULL, role TEXT NOT NULL,
                    label TEXT NOT NULL DEFAULT '', status TEXT NOT NULL,
                    feeding TEXT NOT NULL DEFAULT '[]', joined_at TEXT NOT NULL,
                    PRIMARY KEY(household,user));
                CREATE TABLE IF NOT EXISTS family_invitations (
                    id TEXT PRIMARY KEY, household TEXT NOT NULL, digest TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL, expires_at TEXT NOT NULL, max_uses INTEGER NOT NULL,
                    use_count INTEGER NOT NULL DEFAULT 0, revoked INTEGER NOT NULL DEFAULT 0,
                    invited_by TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS family_invite_accepts (
                    invitation TEXT NOT NULL, user TEXT NOT NULL, PRIMARY KEY(invitation,user));
                CREATE TABLE IF NOT EXISTS family_metadata (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS family_audit (
                    id TEXT PRIMARY KEY, household TEXT NOT NULL, actor TEXT NOT NULL,
                    action TEXT NOT NULL, target TEXT NOT NULL, at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS family_care_access (
                    id TEXT PRIMARY KEY, household TEXT NOT NULL, pet TEXT NOT NULL,
                    creator TEXT NOT NULL, digest TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT);
            """)
            self.conn.execute(
                "INSERT OR IGNORE INTO family_users VALUES (?,?,?,?,?,?)",
                (SEED_USER, "legacy-demo", "disabled", "主人", "", now_iso()),
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO family_households VALUES (?,?,?,?,?)",
                ("demo-owner", "演示家庭", "Asia/Shanghai", SEED_USER, now_iso()),
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO family_memberships VALUES (?,?,?,?,?,?,?)",
                ("demo-owner", SEED_USER, "admin", "主人", "active", '["mochi"]', now_iso()),
            )

    def _load(self, owner: str) -> dict:
        home = super()._load(owner)
        for group in ("measurements", "reports", "memories", "proposals", "occurrences"):
            home.setdefault(group, [])
        home.setdefault("revision", 1)
        home.setdefault("household_id", owner)
        home["device_receipts"] = self.device_receipts(owner)
        home["simulated_device_connected"] = (
            owner == "demo-owner" and self.device_source is not None
        )
        home["members"] = self.members(owner)
        for task in home["tasks"]:
            task.setdefault("version", 1)
            task.setdefault("occurrence_id", new_id())
            task.setdefault("status", "completed" if task["completed"] else "pending")
            task.setdefault("claimed_by", None)
        return home

    def device_receipts(self, owner):
        if owner != "demo-owner" or self.device_source is None:
            return []
        original = self.device_source
        with original.lock:
            if not original.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='receipts'"
            ).fetchone():
                return []
            rows = original.conn.execute(
                "SELECT r.command_id,r.run_id,r.receipt_json,r.created_at,u.proposal_json "
                "FROM receipts r JOIN runs u ON u.run_id=r.run_id WHERE u.owner_id='demo-owner'"
            ).fetchall()
        result = []
        for command, run, receipt_json, at, proposal_json in rows:
            receipt = json.loads(receipt_json)
            action = json.loads(proposal_json)["action"] if proposal_json else {}
            result.append(
                {
                    "id": command,
                    "run_id": run,
                    "pet_id": "mochi",
                    "status": receipt["status"],
                    "simulated": receipt["simulated"],
                    "created_at": at,
                    "kind": action.get("kind"),
                    "grams": action.get("grams", 0),
                }
            )
        return result

    def read(self, owner: str) -> dict:
        with self.lock:
            return self._load(owner)

    def mutate(self, owner: str, change) -> dict:
        def versioned(home):
            before = json.dumps(home, sort_keys=True)
            change(home)
            if json.dumps(home, sort_keys=True) != before:
                home["revision"] += 1
                household = self.household(owner)
                current = [r for r in home["reports"] if r["status"] == "current"]
                for report in current:
                    try:
                        replacement = build_report(
                            home,
                            report["pet_id"],
                            datetime.fromisoformat(report["date"]).date(),
                            report["period"],
                            household,
                        )
                        if report["window_start"] != replacement["window_start"]:
                            report["status"] = "superseded"
                        put_report(home, replacement)
                    except Exception:
                        report["status"] = "failed"
                        report["failure"] = "Statistics rebuild failed; retry generation"

        return super().mutate(owner, versioned)

    def user(self, user_id: str) -> dict:
        with self.lock:
            row = self.conn.execute(
                "SELECT id,username,name,avatar,created_at FROM family_users WHERE id=?", (user_id,)
            ).fetchone()
        if not row:
            raise HTTPException(401, "Account unavailable")
        return dict(
            zip(
                ("user_id", "username", "display_name", "avatar_ref", "created_at"),
                row,
                strict=True,
            )
        )

    def register(self, username: str, password: str, name: str) -> dict:
        uid = new_id()
        hashed = password_hash(password)
        try:
            with self.lock, self.conn:
                self.conn.execute(
                    "INSERT INTO family_users VALUES (?,?,?,?,?,?)",
                    (uid, username.casefold(), hashed, name, "", now_iso()),
                )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, "Username already exists") from exc
        return self.user(uid)

    def authenticate(self, username: str, password: str) -> dict | None:
        with self.lock:
            row = self.conn.execute(
                "SELECT id,password FROM family_users WHERE username=?", (username.casefold(),)
            ).fetchone()
        # A dummy hash reduces account enumeration through timing.
        stored = row[1] if row and row[1].startswith("scrypt$") else password_hash("unavailable")
        computed = password_hash(password, stored.split("$")[1])
        return self.user(row[0]) if row and secrets.compare_digest(stored, computed) else None

    def household(self, household_id: str) -> dict:
        with self.lock:
            row = self.conn.execute(
                "SELECT * FROM family_households WHERE id=?", (household_id,)
            ).fetchone()
        if row is None:
            raise HTTPException(404, "Household not found")
        return dict(
            zip(("household_id", "name", "timezone", "created_by", "created_at"), row, strict=True)
        )

    def membership(self, household_id: str, uid: str) -> dict:
        with self.lock:
            row = self.conn.execute(
                "SELECT role,label,status,feeding,joined_at FROM family_memberships "
                "WHERE household=? AND user=?",
                (household_id, uid),
            ).fetchone()
        if row is None or row[2] != "active":
            raise HTTPException(403, "Household access revoked or unavailable")
        return {
            "user_id": uid,
            "role": row[0],
            "family_label": row[1],
            "status": row[2],
            "feeding_pet_ids": json.loads(row[3]),
            "joined_at": row[4],
        }

    def current_household(self, uid: str) -> str | None:
        with self.lock:
            row = self.conn.execute(
                "SELECT household FROM family_memberships WHERE user=? "
                "AND status='active' ORDER BY joined_at LIMIT 1",
                (uid,),
            ).fetchone()
        return row[0] if row else None

    def members(self, hid: str) -> list[dict]:
        with self.lock:
            rows = self.conn.execute(
                "SELECT user FROM family_memberships WHERE household=? AND status='active'", (hid,)
            ).fetchall()
            return [
                {
                    **self.user(row[0]),
                    **self.membership(hid, row[0]),
                    "id": row[0],
                    "name": self.user(row[0])["display_name"],
                }
                for row in rows
            ]

    def create_household(self, uid: str, name: str, timezone: str) -> dict:
        hid = new_id()
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                if self.current_household(uid):
                    raise HTTPException(409, "Leave your current household before creating another")
                self.conn.execute(
                    "INSERT INTO family_households VALUES (?,?,?,?,?)",
                    (hid, name, timezone, uid, now_iso()),
                )
                self.conn.execute(
                    "INSERT INTO family_memberships VALUES (?,?,?,?,?,?,?)",
                    (hid, uid, "admin", "", "active", "[]", now_iso()),
                )
                home = initial_home()
                home["members"] = []
                home["household_id"] = hid
                self.conn.execute(
                    "INSERT INTO pet_home_documents VALUES (?,?)", (hid, json.dumps(home))
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise
        return self.household(hid)

    def update_profile(self, uid: str, hid: str | None, body: dict) -> None:
        with self.lock, self.conn:
            if body.get("display_name") is not None:
                self.conn.execute(
                    "UPDATE family_users SET name=? WHERE id=?", (body["display_name"], uid)
                )
            if body.get("avatar_ref") is not None:
                self.conn.execute(
                    "UPDATE family_users SET avatar=? WHERE id=?", (body["avatar_ref"], uid)
                )
            if hid and body.get("family_label") is not None:
                self.membership(hid, uid)
                self.conn.execute(
                    "UPDATE family_memberships SET label=? WHERE household=? AND user=?",
                    (body["family_label"], hid, uid),
                )

    def invite(self, hid: str, uid: str, body: dict) -> dict:
        token, iid = secrets.token_urlsafe(32), new_id()
        expires = (datetime.now(UTC) + timedelta(hours=body["expires_in_hours"])).isoformat()
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT INTO family_invitations "
                "(id,household,digest,role,expires_at,max_uses,invited_by) VALUES (?,?,?,?,?,?,?)",
                (
                    iid,
                    hid,
                    hashlib.sha256(token.encode()).hexdigest(),
                    body["role"],
                    expires,
                    body["max_uses"],
                    uid,
                ),
            )
        return {"invitation_id": iid, "token": token, "expires_at": expires, "role": body["role"]}

    def accept(self, uid: str, token: str) -> str:
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                row = self.conn.execute(
                    "SELECT id,household,role,expires_at,max_uses,use_count,revoked "
                    "FROM family_invitations WHERE digest=?",
                    (hashlib.sha256(token.encode()).hexdigest(),),
                ).fetchone()
                if not row or row[6] or parse(row[3]) <= datetime.now(UTC):
                    raise HTTPException(410, "Invitation expired, revoked or unavailable")
                accepted = self.conn.execute(
                    "SELECT 1 FROM family_invite_accepts WHERE invitation=? AND user=?",
                    (row[0], uid),
                ).fetchone()
                if accepted:
                    self.membership(row[1], uid)  # A removed member cannot reuse an old acceptance.
                    self.conn.commit()
                    return row[1]
                if row[5] >= row[4]:
                    raise HTTPException(410, "Invitation exhausted")
                current = self.current_household(uid)
                if current and current != row[1]:
                    raise HTTPException(409, "Leave your current household first")
                existing = self.conn.execute(
                    "SELECT status FROM family_memberships WHERE household=? AND user=?",
                    (row[1], uid),
                ).fetchone()
                if existing and existing[0] == "active":
                    self.conn.commit()
                    return row[1]
                self.conn.execute(
                    "INSERT OR REPLACE INTO family_memberships VALUES (?,?,?,?,?,?,?)",
                    (row[1], uid, row[2], "", "active", "[]", now_iso()),
                )
                self.conn.execute("INSERT INTO family_invite_accepts VALUES (?,?)", (row[0], uid))
                self.conn.execute(
                    "UPDATE family_invitations SET use_count=use_count+1 WHERE id=?", (row[0],)
                )
                self.conn.commit()
                return row[1]
            except Exception:
                self.conn.rollback()
                raise

    def change_member(
        self,
        hid: str,
        uid: str,
        *,
        role: str | None = None,
        feeding: list | None = None,
        remove: bool = False,
    ) -> None:
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                member = self.membership(hid, uid)
                count = self.conn.execute(
                    "SELECT count(*) FROM family_memberships WHERE household=? "
                    "AND role='admin' AND status='active'",
                    (hid,),
                ).fetchone()[0]
                if member["role"] == "admin" and count == 1 and (remove or role != "admin"):
                    raise HTTPException(
                        409, "Transfer administration before leaving or demoting the last admin"
                    )
                if feeding and hid != "demo-owner":
                    raise HTTPException(
                        422, "Only the seed household has a simulated feeding device"
                    )
                self.conn.execute(
                    "UPDATE family_memberships SET role=?,status=?,feeding=? "
                    "WHERE household=? AND user=?",
                    (
                        role or member["role"],
                        "removed" if remove else "active",
                        json.dumps(feeding if feeding is not None else member["feeding_pet_ids"]),
                        hid,
                        uid,
                    ),
                )
                if remove or (role is not None and role != "admin"):
                    self.conn.execute(
                        "UPDATE family_care_access SET revoked_at=? "
                        "WHERE household=? AND creator=? AND revoked_at IS NULL",
                        (now_iso(), hid, uid),
                    )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

    def audit(self, hid: str, uid: str, action: str, target: str) -> None:
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT INTO family_audit VALUES (?,?,?,?,?,?)",
                (new_id(), hid, uid, action, target, now_iso()),
            )

    @staticmethod
    def _grant(row) -> dict:
        return dict(zip(
            ("id", "household", "pet", "creator", "digest",
             "created_at", "expires_at", "revoked_at"),
            row, strict=True,
        ))

    def create_care_access(self, hid, pet_id, creator, hours=24) -> tuple[str, dict]:
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                if self.membership(hid, creator)["role"] != "admin":
                    raise HTTPException(403, "Household administrator required")
                pet = next((p for p in self._load(hid)["pets"] if p["id"] == pet_id), None)
                if pet is None or pet.get("archived_at"):
                    raise HTTPException(404, "Pet not found")
                token = secrets.token_urlsafe(32)
                now = datetime.now(UTC)
                row = (
                    new_id(), hid, pet_id, creator, hashlib.sha256(token.encode()).hexdigest(),
                    now.isoformat(), (now + timedelta(hours=hours)).isoformat(), None,
                )
                self.conn.execute("INSERT INTO family_care_access VALUES (?,?,?,?,?,?,?,?)", row)
                self.conn.execute("INSERT INTO family_audit VALUES (?,?,?,?,?,?)", (
                    new_id(), hid, creator, "care_access_created", row[0], now.isoformat(),
                ))
                self.conn.commit()
                return token, self._grant(row)
            except Exception:
                self.conn.rollback()
                raise

    def care_access_list(self, hid, pet_id) -> list[dict]:
        with self.lock:
            return [self._grant(r) for r in self.conn.execute(
                "SELECT * FROM family_care_access WHERE household=? AND pet=? "
                "ORDER BY created_at DESC",
                (hid, pet_id),
            ).fetchall()]

    def care_access_status(self, grant, home=None, now=None) -> str:
        now = now or datetime.now(UTC)
        if grant["revoked_at"]:
            return "revoked"
        issuer = self.conn.execute(
            "SELECT role,status FROM family_memberships WHERE household=? AND user=?",
            (grant["household"], grant["creator"]),
        ).fetchone()
        if issuer != ("admin", "active"):
            return "revoked"
        if parse(grant["expires_at"]) <= now:
            return "expired"
        home = home if home is not None else self._load(grant["household"])
        pet = next((p for p in home["pets"] if p["id"] == grant["pet"]), None)
        return "pet_archived" if pet is None or pet.get("archived_at") else "active"

    def resolve_care_access(self, token) -> tuple[dict, dict]:
        with self.lock:
            row = self.conn.execute(
                "SELECT * FROM family_care_access WHERE digest=?",
                (hashlib.sha256(token.encode()).hexdigest(),),
            ).fetchone()
            if row is None:
                raise HTTPException(401, "Care access key is invalid")
            grant = self._grant(row)
            home = self._load(grant["household"])
            if self.care_access_status(grant, home) != "active":
                raise HTTPException(410, "Care access is no longer available")
            return grant, home

    def revoke_care_access(self, hid, pet_id, access_id, actor) -> dict:
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                if self.membership(hid, actor)["role"] != "admin":
                    raise HTTPException(403, "Household administrator required")
                row = self.conn.execute(
                    "SELECT * FROM family_care_access WHERE id=? AND household=? AND pet=?",
                    (access_id, hid, pet_id),
                ).fetchone()
                if row is None:
                    raise HTTPException(404, "Access grant not found")
                grant = self._grant(row)
                if not grant["revoked_at"]:
                    grant["revoked_at"] = now_iso()
                    self.conn.execute(
                        "UPDATE family_care_access SET revoked_at=? WHERE id=?",
                        (grant["revoked_at"], access_id),
                    )
                    self.conn.execute("INSERT INTO family_audit VALUES (?,?,?,?,?,?)", (
                        new_id(), hid, actor, "care_access_revoked", access_id, grant["revoked_at"],
                    ))
                self.conn.commit()
                return grant
            except Exception:
                self.conn.rollback()
                raise

    def import_legacy(self, original: HomeStore) -> dict:
        with self.lock:
            if self.conn.execute(
                "SELECT 1 FROM family_metadata WHERE key='legacy_import_v1'"
            ).fetchone():
                return {"already_imported": True}
        # SQLite backup includes committed WAL pages; source content is never rewritten.
        with original.lock:
            source_path = original.conn.execute("PRAGMA database_list").fetchone()[2]
            if source_path:
                source = Path(source_path)
                stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
                backup_path = source.with_name(source.name + f".before-family-{stamp}.bak")
                with sqlite3.connect(backup_path) as backup:
                    original.conn.backup(backup)
            row = original.conn.execute(
                "SELECT document FROM pet_home_documents WHERE owner='demo-owner'"
            ).fetchone()
            source = json.loads(row[0]) if row else initial_home()
            photos = original.conn.execute(
                "SELECT id,mime,image FROM pet_home_photos WHERE owner='demo-owner'"
            ).fetchall()
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                if self.conn.execute(
                    "SELECT 1 FROM family_metadata WHERE key='legacy_import_v1'"
                ).fetchone():
                    self.conn.commit()
                    return {"already_imported": True}
                source["household_id"] = "demo-owner"
                # A worker from an older build may have advanced a synthetic seed cursor.
                self.conn.execute(
                    "DELETE FROM family_metadata WHERE key LIKE 'reports:demo-owner:%'"
                )
                source["legacy_members"] = source["members"]
                names = {m["id"]: m["name"] for m in source["members"]}
                for group in ("notes", "diary", "history"):
                    for item in source[group]:
                        item["legacy_actor_id"] = item.get("actor_id")
                        item["author_user_id"] = item.get("actor_id", "legacy-unknown")
                        item["author_name"] = names.get(
                            item.get("actor_id"), item.get("actor", "原记录人未知")
                        )
                        item["household_id"] = "demo-owner"
                self.conn.execute(
                    "INSERT OR REPLACE INTO pet_home_documents VALUES (?,?)",
                    ("demo-owner", json.dumps(source, ensure_ascii=False)),
                )
                for pid, mime, image in photos:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO pet_home_photos VALUES (?,?,?,?)",
                        (pid, "demo-owner", mime, image),
                    )
                result = {g: len(source[g]) for g in ("pets", "tasks", "diary", "notes", "history")}
                result["photos"] = len(photos)
                result["already_imported"] = False
                self.conn.execute(
                    "INSERT INTO family_metadata VALUES ('legacy_import_v1',?)",
                    (json.dumps(result),),
                )
                self.conn.commit()
                return result
            except Exception:
                self.conn.rollback()
                raise

    def generate(self, hid: str, pet_id: str, day, period: str, now=None) -> dict:
        result = {}

        def change(home):
            report = build_report(home, pet_id, day, period, self.household(hid), now)
            result.update(put_report(home, report))

        # Report generation itself does not change source revision.
        HomeStore.mutate(self, hid, change)
        return result

    def refresh_reports(self, hid, now=None):
        home = self.read(hid)
        for report in [r for r in home["reports"] if r["status"] == "current"]:
            self.generate(
                hid,
                report["pet_id"],
                datetime.fromisoformat(report["date"]).date(),
                report["period"],
                now,
            )

    def run_due_reports(self, now: datetime | None = None) -> int:
        if self.device_source is not None:
            # Import before reporting, even when no browser has opened the old home yet.
            self.import_legacy(self.device_source)
        now = now or datetime.now(UTC)
        count = 0
        with self.lock:
            households = self.conn.execute("SELECT id FROM family_households").fetchall()
        for (hid,) in households:
            self.refresh_reports(hid, now)
            household = self.household(hid)
            today = now.astimezone(ZoneInfo(household["timezone"])).date()
            home = self.read(hid)
            failed = [r for r in home["reports"] if r["status"] == "failed"]
            for report in failed:
                self.generate(
                    hid,
                    report["pet_id"],
                    datetime.fromisoformat(report["date"]).date(),
                    report["period"],
                    now,
                )
                HomeStore.mutate(
                    self,
                    hid,
                    lambda h, rid=report["report_id"]: next(
                        r for r in h["reports"] if r["report_id"] == rid
                    ).update(status="superseded"),
                )
            for pet in home["pets"]:
                if pet.get("archived_at"):
                    continue
                key = f"reports:{hid}:{pet['id']}"
                with self.lock:
                    row = self.conn.execute(
                        "SELECT value FROM family_metadata WHERE key=?", (key,)
                    ).fetchone()
                # Bootstrap yesterday, then persist a cursor for restart catch-up.
                day = (
                    datetime.fromisoformat(row[0]).date() + timedelta(days=1)
                    if row
                    else today - timedelta(days=1)
                )
                while day < today:
                    self.generate(hid, pet["id"], day, "daily", now)
                    if day.weekday() == 6:
                        self.generate(hid, pet["id"], day, "weekly", now)
                    with self.lock, self.conn:
                        self.conn.execute(
                            "INSERT OR REPLACE INTO family_metadata VALUES (?,?)",
                            (key, day.isoformat()),
                        )
                    count += 1
                    day += timedelta(days=1)
        return count


class LegacyHomeView:
    """Legacy display-name compatibility over the same migrated household document."""

    def __init__(self, family: FamilyStore, source: HomeStore):
        self.family = family
        self.source = source

    def read(self, owner: str):
        self.family.import_legacy(self.source)
        home = self.family.read(owner)
        home["members"] = home.get("legacy_members", [])
        return home

    def mutate(self, owner: str, change):
        self.family.import_legacy(self.source)

        def legacy_change(home):
            home["members"] = home.get("legacy_members", [])
            change(home)
            home["legacy_members"] = home["members"]

        result = self.family.mutate(owner, legacy_change)
        result["members"] = result.get("legacy_members", [])
        return result

    def photo(self, owner: str, photo_id: str):
        self.family.import_legacy(self.source)
        return self.family.photo(owner, photo_id)

    def save_photo(self, owner: str, mime: str, image: bytes):
        self.family.import_legacy(self.source)
        return self.family.save_photo(owner, mime, image)

    def close(self):
        # Owned and closed by application lifespan, once each.
        pass
