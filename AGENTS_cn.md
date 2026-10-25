# AGENTS_cn.md — 智能体规则（中文对照；以英文 `AGENTS.md` 为准）

## 闭环
1. 运行 `python tools/next.py`，只做它给出的这一件事。
2. 在 `loop/<任务ID>` 分支上工作（issue 用 `fix/I-xxx`）；修 bug 先写红灯检查。
3. 改了代码或数据，就在 `pipeline.yaml` 增改对应步骤并运行 `make all`。
4. `make gates` 必须全绿；PR 写明任务和 `done_when` 验收标准。
5. 涉及研究目标、写作法规、例外、对已合并工作的科学改动、推翻核心理论时，标 `needs-user` 等负责人，不要猜。

## 角色（查新对手和审计员须与提出者使用不同模型）
理论（THEORY.md）· 对手（NOVELTY.md，目标是证明“不新”）· 实验（src、E-xxx、run 的流水线步骤）· 审计（audit/reports）· 裁判（只追加 claims.yaml）· 绘图（plot、图步骤）· 写作（writing/tex）· 负责人（STUDY.yaml、写作法规、EXCEPTIONS）。

## 硬规则（`make gates` 强制）
1. **数据**：raw 只增不改，文件名以内容 sha256 前 16 位开头；derived、figure_data、runs 只能由 `pipeline.yaml` 步骤产生且与 `pipeline.lock` 一致。
2. **预登记**：正式 run 需要已锁定且声明 holdout 的 PREREG；锁定后不可改。
3. **证据**：claims.yaml 只追加；supported / refuted / inconclusive 必须引用审计 pass 的正式 run；探索结果不入证据、图和正文，只有 dead-end 可引用；预登记中的理论须查新判定 novel 或 incremental、列 5 篇最近工作、对手与提出者模型不同；未经 novel + 负责人抽查禁用新颖性措辞。
4. **图**：fast 步骤只读 figure_data/ 和 plot/；每图有同名描述，数字自动填；绘图 CSV 每列在 README 说明。
5. **卫生**：中文只在 `*_cn.md` 且有英文同名文件；禁止本机绝对路径、外部软链接、密钥、`os.chdir`。

## 其他
科学等价改动单独 PR 并标 `needs-user`；未运行的检查不得写成通过；正文数字来自 `writing/tex/gen/numbers.tex`。
环境：`pypardiso` 可选（仅 x86_64，否则走 scipy）；保持 `MKL_CBWR=AUTO,STRICT`（`src/kkt.py` 与 `tools/prun2.py` 中设置），使结果与线程数无关；改动 `src/kkt.py` 后运行 `python tests/test_kkt.py`。
