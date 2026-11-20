# 002 月结抽查

- 新表 `sample_plans`（SQLAlchemy 启动 create_all 自动建立）：`run_id` 唯一约束保证每份报告只锁一次名额与系统随机起点；`random_start`、`pool_total_cents` 为 BIGINT（整数分，放大轴）；`status` 为 locked/published；`result` JSON 保存样本与逐笔精确概率。
- `allocationruns.snapshot` 自本版本起新增 `voucher_keys`（与 `sources` 同序的凭证自然键）。仅影响新提交报告；旧报告快照不变。
- 旧格式快照（无 `voucher_keys`）在抽查接口被拒绝并说明原因；seed 内置一份“十月旧格式报告（缺凭证身份）”用于演示拒抽。
- 核对：`python -m scripts.verify_sampling` 穷举小账全部起点核对逐笔精确概率，并检查并发只锁一份、重跑不重复发布、崩溃恢复沿用原起点。
