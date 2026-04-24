# Phase 6 测试记录

> 目标：验证第一版在多类型文档输入下的稳定性和可演示性。

---

## 一、测试范围

- 输入类型：
  - meeting notes
  - PRD excerpt
  - email thread
  - SOP note
  - mixed notes
- 功能范围：
  - 输入与分析
  - 四类结构化输出
  - 引用依据查看
  - 人工编辑（summary + action items）
  - Markdown 导出

---

## 二、测试样本清单

- `samples/meeting_notes.md`
- `samples/prd_excerpt.md`
- `samples/email_thread.md`
- `samples/sop_note.md`
- `samples/mixed_notes.md`

---

## 三、执行方式

### 方式 A：页面手测

1. 启动前后端服务
2. 在页面中逐个上传样本
3. 记录输出质量与异常情况

### 方式 B：脚本批量检查

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=.. python ../scripts/run_sample_checks.py
```

输出目录：

- `learning/报告与演示材料/demo/phase6-sample-report.md`
- `learning/报告与演示材料/demo/*.result.json`

---

## 四、测试记录模板

### 样本：`<file-name>`

- 输出是否成功：是 / 否
- Summary 是否可读：是 / 否
- Action Items 是否具备执行性：高 / 中 / 低
- Risks 是否合理：高 / 中 / 低
- Open Questions 是否有价值：高 / 中 / 低
- 引用依据是否可点击：是 / 否
- 编辑是否可用：是 / 否
- 导出是否成功：是 / 否
- 问题与备注：

---

## 五、回归检查清单

- [ ] 无输入时 Analyze 不可点击
- [ ] Analyze loading 状态正常
- [ ] 接口失败时 error 提示可见
- [ ] 点击条目可显示引用 chunk
- [ ] 无引用条目有提示
- [ ] 可新增/删除 action item
- [ ] 编辑后导出内容与页面一致

---

## 六、结论

- 当前版本稳定性：主流程可稳定跑通（脚本批量运行成功，5/5 样本有输出）
- 主要问题：
  - 降级规则下有“关键词误判”情况（如 email 主题可能被识别为 risk）
  - action / risk 边界在混合文本中偶有重叠
  - 目前仅 action items 支持编辑，risk/question 仍为只读
- 改进优先级（P0/P1/P2）：
  - P0：优化规则提取精度，减少误判
  - P1：补充 risk/open question 编辑能力
  - P2：增加输出质量评分与样本对比仪表
