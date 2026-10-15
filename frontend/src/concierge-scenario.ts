// The showcase and workbench play the same illustrative story.
export const CONCIERGE_STEPS = [
  { label: '小狗饮食', title: '这只小狗，能吃巧克力吗？', status: '预设对话', detail: '识别 Miso 的柯基档案，说明巧克力风险，再参考已确认的鸡肉偏好给出替代选择。' },
  { label: '猫咪状态', title: '猫咪没精神，先看哪些记录？', status: '模拟记录', detail: '结合 Luna 的档案和模拟活动记录给出观察项；活动接近平日，也不能据此排除生病。' },
  { label: '上下文随行', title: '少一次介绍，多一份了解。', status: '上下文示意', detail: '对比没有宠物资料的新会话：同一个问题，在这里可以自动带上已保存的档案、确认偏好和记录来源。' },
]
