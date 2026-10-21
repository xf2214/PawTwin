import { t } from "./i18n";
import { actorName } from "./system-defaults";
import type { Diary, Home, Note } from "./family-api";
import { familyDay, familyTime } from "./family-time";

type Props = {
  home: Home;
  petId: string;
  userId: string;
  admin: boolean;
  canWrite: boolean;
  busy: boolean;
  timezone: string;
  act: (action: () => Promise<unknown>, message?: string) => Promise<boolean>;
  mutate: (path: string, body?: object, method?: string) => Promise<unknown>;
};
const value = (data: FormData, key: string) => String(data.get(key) ?? "");

export default function FamilyRecords({
  home,
  petId,
  userId,
  admin,
  canWrite,
  busy,
  timezone,
  act,
  mutate,
}: Props) {
  const editable = (record: Note | Diary) =>
    canWrite && (admin || record.author_user_id === userId);
  const notes = home.notes.filter((n) => n.pet_id === petId);
  const diary = home.diary.filter((d) => d.pet_id === petId);
  function remove(group: string, record: Note | Diary) {
    return act(
      () =>
        mutate(
          `/api/family/pets/${petId}/${group}/${record.id}?version=${record.version ?? 1}`,
          undefined,
          "DELETE",
        ),
      "记录已删除，统计与分身已更新",
    );
  }
  return (
    <section className="fa-card" aria-label={t("观察与日记管理")}>
      <h2>{t("观察与日记管理")}</h2>
      <p>{t("保留当时作者和修订历史；修改后的有效内容同步用于统计和分身。")}</p>
      {!notes.length && !diary.length && (
        <p>{t("还没有观察或日记，可在小屋记录。")}</p>
      )}
      {notes.map((n) => (
        <article className="fa-record" key={n.id}>
          <strong>{n.text}</strong>
          <p>
            {actorName(n.author_name, n.author_user_id) || t("历史记录")} ·{" "}
            {{
              today: t("仅今天"),
              preference: t("确认偏好"),
              observation: t("一般观察"),
            }[n.scope] ?? n.scope}
            {n.scope === "today" && familyDay(n.created_at, timezone) !== familyDay(new Date(), timezone) ? t(" · 已过期，不再用于当前建议") : ""}
          </p>
          <small>{familyTime(n.created_at, timezone)}</small>
          {editable(n) && (
            <details>
              <summary>{t("纠正观察")}</summary>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const d = new FormData(e.currentTarget);
                  void act(() =>
                    mutate(
                      `/api/family/pets/${petId}/notes/${n.id}`,
                      {
                        version: n.version ?? 1,
                        text: value(d, "text"),
                        scope: value(d, "scope"),
                        activity: n.activity,
                      },
                      "PATCH",
                    ),
                  );
                }}
              >
                <label>{t("修订观察原文")} <textarea
                    name="text"
                    required
                    maxLength={500}
                    defaultValue={n.text}
                  />
                </label>
                <label>{t("观察有效范围")} <select name="scope" defaultValue={n.scope}>
                    <option value="today">{t("仅今天")}</option>
                    <option value="observation">{t("一般观察")}</option>
                    <option value="preference">{t("确认偏好")}</option>
                  </select>
                </label>
                <button disabled={busy}>{t("保存观察修订")}</button>
                <button
                  type="button"
                  disabled={busy}
                  className="fa-secondary"
                  onClick={() => void remove("notes", n)}
                >{t("删除观察")} </button>
              </form>
            </details>
          )}
        </article>
      ))}
      {diary.map((d) => (
        <article className="fa-record" key={d.id}>
          <strong>{d.title}</strong>
          <p>{d.text}</p>
          <small>
            {d.happened_on} · {actorName(d.author_name, d.author_user_id) || t("历史记录")}
          </small>
          {editable(d) && (
            <details>
              <summary>{t("纠正日记")}</summary>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const f = new FormData(e.currentTarget);
                  void act(() =>
                    mutate(
                      `/api/family/pets/${petId}/diary/${d.id}`,
                      {
                        version: d.version ?? 1,
                        title: value(f, "title"),
                        text: value(f, "text"),
                        happened_on: value(f, "date"),
                        photo_id: d.photo_id,
                      },
                      "PATCH",
                    ),
                  );
                }}
              >
                <label>{t("修订日记标题")} <input
                    name="title"
                    required
                    maxLength={80}
                    defaultValue={d.title}
                  />
                </label>
                <label>{t("修订日记内容")} <textarea
                    name="text"
                    maxLength={2000}
                    defaultValue={d.text}
                  />
                </label>
                <label>{t("修订日记日期")} <input
                    name="date"
                    type="date"
                    required
                    defaultValue={d.happened_on}
                  />
                </label>
                <button disabled={busy}>{t("保存日记修订")}</button>
                <button
                  type="button"
                  disabled={busy}
                  className="fa-secondary"
                  onClick={() => void remove("diary", d)}
                >{t("删除日记")} </button>
              </form>
            </details>
          )}
        </article>
      ))}
    </section>
  );
}
