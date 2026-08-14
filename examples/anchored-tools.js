// ============================================================
// Anchored Tool Catalog 示例：引导工具 vs 标准工具
// 两阶段工具目录开启后：
//   bootstrap 阶段 → 模型只看到 anchor: true 的工具
//   第一次工具调用后 → 自动晋升 full，所有工具可见
// ============================================================

// --- 引导工具（bootstrap 阶段可见）---
// 建议放“读取/检索类”的轻量工具，不要放容易带偏轨迹的大动作工具

return {
    name: 'read_lore',
    displayName: '查阅设定',
    description: '读取当前角色/场景相关的设定条目，用于回答涉及世界观细节的问题。',
    anchor: true,                       // ← 关键：标记为引导工具
    parameters: {
        type: 'object',
        properties: {
            topic: { type: 'string', description: '要查阅的设定主题' },
        },
        required: ['topic'],
    },
    action: async (args, api) => {
        api.util.log('查阅设定:', args.topic);
        await api.reply.appendReasoning(`\n[查阅设定] ${args.topic}`);
        return JSON.stringify({ ok: true, topic: args.topic, note: '这里换成实际的世界书查询逻辑' });
    },
};

// 注意：每个世界书条目只能 return 一个工具定义。
// 要加第二个引导工具，请在另一个世界书条目里再写一段，同样带上 anchor: true。
// 也可以不写 anchor，而是在扩展设置里配置“引导工具白名单”（逗号分隔工具 name）。
