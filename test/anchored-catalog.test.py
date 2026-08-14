# -*- coding: utf-8 -*-
"""
Anchored Tool Catalog 逻辑验证（Python 模拟）
等价复刻 tool-runtime.js 中的门控逻辑，验证各场景行为。
"""
import sys

# ---- 复刻 tool-runtime.js 的门控状态与函数 ----
class AnchoredCatalog:
    def __init__(self):
        self.enabled = False
        self.phase = 'full'
        self.whitelist = None      # set | None
        self.promotion_calls = 0   # 晋升回调触发次数

    def configure(self, enabled=False, anchor_names=None):
        self.enabled = bool(enabled)
        self.whitelist = set(n.strip() for n in anchor_names if n and n.strip()) if anchor_names else None

    def set_phase(self, phase, silent=False):
        nxt = 'bootstrap' if phase == 'bootstrap' else 'full'
        if self.phase == nxt:
            return
        self.phase = nxt
        if not silent:
            self.promotion_calls += 1

    def is_anchor(self, tool_def):
        if self.whitelist:
            return tool_def['name'] in self.whitelist or tool_def.get('displayName', '') in self.whitelist
        return tool_def.get('anchor') is True

    def should_expose(self, tool_def):
        if not self.enabled:
            return True
        if self.phase == 'full':
            return True
        return self.is_anchor(tool_def)

    # ---- 晋升触发点 ----
    def on_has_tool_calls(self, has):
        if has and self.enabled and self.phase == 'bootstrap':
            self.set_phase('full')

    def on_begin_tool_invocation(self):
        if self.enabled and self.phase == 'bootstrap':
            self.set_phase('full')

# ---- 测试工具 ----
tools = [
    {'name': 'read', 'description': '读文件', 'parameters': {}, 'action': None, 'anchor': True},
    {'name': 'search', 'description': '搜索', 'parameters': {}, 'action': None, 'anchor': True},
    {'name': 'execute', 'description': '执行命令', 'parameters': {}, 'action': None},
    {'name': 'write_file', 'description': '写文件', 'parameters': {}, 'action': None},
]

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1; print(f'  PASS  {name}')
    else: failed += 1; print(f'  FAIL  {name}')

print('=== 场景 1：未开启门控（默认行为不变）===')
c = AnchoredCatalog()  # enabled=False, phase=full
visible = [t['name'] for t in tools if c.should_expose(t)]
check('全部工具可见', visible == ['read','search','execute','write_file'])

print('=== 场景 2：开启 + bootstrap + anchor 标记 ===')
c = AnchoredCatalog(); c.configure(enabled=True); c.set_phase('bootstrap', silent=True)
visible = [t['name'] for t in tools if c.should_expose(t)]
check('只暴露 anchor 工具', visible == ['read','search'])

print('=== 场景 3：开启 + bootstrap + 白名单 ===')
c = AnchoredCatalog(); c.configure(enabled=True, anchor_names=['execute']); c.set_phase('bootstrap', silent=True)
visible = [t['name'] for t in tools if c.should_expose(t)]
check('只暴露白名单工具', visible == ['execute'])

print('=== 场景 4：bootstrap 无任何引导工具（空目录兜底）===')
c = AnchoredCatalog(); c.configure(enabled=True); c.set_phase('bootstrap', silent=True)
no_anchor_tools = [dict(t) for t in tools]
for t in no_anchor_tools:
    t.pop('anchor', None)  # 全部工具都不带 anchor，也无白名单
visible = [t['name'] for t in no_anchor_tools if c.should_expose(t)]
check('全部不可见（触发警告场景）', visible == [])
check('存在应警告条件（有工具但无 anchor）', len(no_anchor_tools) == 4 and not any(c.is_anchor(t) for t in no_anchor_tools))

print('=== 场景 5：工具执行 → 晋升 full → 全部可见 ===')
c = AnchoredCatalog(); c.configure(enabled=True); c.set_phase('bootstrap', silent=True)
check('晋升前 bootstrap', c.phase == 'bootstrap')
c.on_begin_tool_invocation()  # 等价 beginToolInvocation
check('工具执行后晋升 full', c.phase == 'full')
visible = [t['name'] for t in tools if c.should_expose(t)]
check('晋升后全部工具可见', visible == ['read','search','execute','write_file'])
check('晋升回调恰好触发一次', c.promotion_calls == 1)

print('=== 场景 6：hasToolCalls 检测晋升（模型发 tool_calls 即晋升）===')
c = AnchoredCatalog(); c.configure(enabled=True); c.set_phase('bootstrap', silent=True)
c.on_has_tool_calls(False)  # 模型没调工具
check('无 tool_calls 不晋升', c.phase == 'bootstrap')
c.on_has_tool_calls(True)
check('有 tool_calls 晋升', c.phase == 'full')
c.on_has_tool_calls(True)  # 幂等
check('重复检测幂等，回调不重复触发', c.promotion_calls == 1)

print('=== 场景 7：metadata 恢复（restoreAnchoredPhaseFromMetadata 三分支）===')
# 分支 A：有记录 full
c = AnchoredCatalog(); c.configure(enabled=True)
stored = 'full'; phase = stored if stored in ('bootstrap','full') else ('bootstrap' if c.enabled else 'full')
c.set_phase(phase, silent=True)
check('记录 full → 恢复 full', c.phase == 'full')
# 分支 B：无记录 + 开启 → bootstrap
c = AnchoredCatalog(); c.configure(enabled=True)
stored = None; phase = stored if stored in ('bootstrap','full') else ('bootstrap' if c.enabled else 'full')
c.set_phase(phase, silent=True)
check('新聊天 + 开启 → bootstrap', c.phase == 'bootstrap')
# 分支 C：无记录 + 关闭 → full
c = AnchoredCatalog(); c.configure(enabled=False)
stored = None; phase = stored if stored in ('bootstrap','full') else ('bootstrap' if c.enabled else 'full')
c.set_phase(phase, silent=True)
check('新聊天 + 关闭 → full（内部一致）', c.phase == 'full')

print()
print(f'结果: {passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
