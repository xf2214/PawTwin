import { locale } from './i18n';

export const CARE: Record<string, string> = {
  feeding: "人工喂食", water: "换水", play: "陪玩", brush: "梳毛",
  bath: "洗澡", nails: "剪指甲", clean: "清洁", walk: "散步",
};

export function browserInput(value: string | Date = new Date()) {
  const date = new Date(value);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

export function familyDay(value: string | Date, timezone: string) {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: timezone, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date(value));
  const part = (name: string) => parts.find(p => p.type === name)?.value;
  return `${part("year")}-${part("month")}-${part("day")}`;
}

export function familyTime(value: string, timezone: string) {
  return new Intl.DateTimeFormat(locale(), { timeZone: timezone, year: "numeric", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(value));
}

export const APP_TABS: Record<string, string> = { 小屋: "home", 照护: "care", 成长: "growth", 助手: "assistant", 家庭: "family" };
export const APP_LABELS: Record<string, string> = { 小屋: "今日", 照护: "照护", 成长: "成长", 助手: "分身", 家庭: "家庭" };
export function appTab(hash = window.location.hash) {
  if (hash === "#alexa") return "Alexa+";
  return Object.entries(APP_TABS).find(([, path]) => hash === `#app/${path}`)?.[0] ?? "小屋";
}
