import { t } from './i18n'
import type { Me } from './family-api'

const demoUser = '00000000-0000-4000-8000-000000000001'

// These identities come from the built-in demo, not from household input.
export function actorName(value: string, userId?: string | null): string {
  if (userId === demoUser && value === '主人') return t('主人', 'Owner')
  if (userId === 'demo-owner' && value === '主人（演示登录）') return t('主人（演示登录）', 'Owner (demo sign-in)')
  if (!userId && value === '原记录人未知') return t('原记录人未知', 'Original author unknown')
  return value
}

export function localizeDemoMe(me: Me): Me {
  const member = (item: NonNullable<Me['membership']>) => ({
    ...item,
    display_name: actorName(item.display_name, item.user_id),
    family_label: actorName(item.family_label, item.user_id),
  })
  return {
    ...me,
    user: { ...me.user, display_name: actorName(me.user.display_name, me.user.user_id) },
    household: me.household ? {
      ...me.household,
      name: me.household.household_id === 'demo-owner' && me.household.name === '演示家庭'
        ? t('演示家庭', 'Demo household') : me.household.name,
    } : null,
    membership: me.membership ? member(me.membership) : null,
    members: me.members.map(member),
  }
}

const starterItems: Record<string, { name: string; note: string; englishName: string; englishNote: string }> = {
  nest: { name: '窗边小窝', note: '初始展示物品，可修改', englishName: 'Window bed', englishNote: 'Starter display item; you can edit it' },
  toy: { name: '羽毛棒', note: '初始展示物品，可修改', englishName: 'Feather wand', englishNote: 'Starter display item; you can edit it' },
  feeder: { name: '模拟喂食器', note: '模拟设备，不连接真实硬件', englishName: 'Simulated feeder', englishNote: 'Simulated device; no real hardware connected' },
  water: { name: '水碗', note: '初始展示物品，可修改', englishName: 'Water bowl', englishNote: 'Starter display item; you can edit it' },
}

export function itemText(item: { kind: string; name: string; note: string }, field: 'name' | 'note'): string {
  const starter = starterItems[item.kind]
  // Match the complete starter signature. A renamed item or owner-written note
  // is ordinary user content, even if one field happens to match a starter.
  if (!starter || item.name !== starter.name || item.note !== starter.note) return item[field]
  return t(item[field], field === 'name' ? starter.englishName : starter.englishNote)
}
