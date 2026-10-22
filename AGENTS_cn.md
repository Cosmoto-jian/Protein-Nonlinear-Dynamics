# AGENTS_cn.md — 智能体导航（中文对照；以英文 `AGENTS.md` 为准）

## 研究主题
见 `STUDY.yaml`。所有工作服务于其中的 `question` 与 `aims`；偏离即开 `scope` issue。

## 硬规则
1. 结论只能引用 `research/experiment/E-xxx/runs/` 下的 run ID；`explore/` 结果永不作证据。
2. `PREREG.yaml` 在首个 run 前提交，之后不可修改（门禁比对 git 历史）。
3. `data/raw/` 文件名以内容 sha256 前缀开头；只增不改不删。
4. 理论进入预登记前，`NOVELTY.md` 判定须为 `novel` 或 `incremental`。
5. `incremental` 工作禁用 “first / novel / for the first time”。
6. 每张图有同名描述，数字从数据自动填充，不手写。
7. 修改研究目标、写作法规或推翻 core 理论 → `needs-user`，等负责人批准。
8. 语言隔离：代码、配置、数据、文件名、英文文档不含中文；中文只在 `*_cn.md`，且须有纯英文同名文件。
9. 可移植：禁止本机绝对路径、指向仓库外的软链接、密钥、`os.chdir`；所有命令从项目根目录运行。
10. 绘图脚本只读 `figure_data/`；`plot/extract/` 是 run → 绘图数据的唯一通道。每个绘图 CSV 在所在目录 README 写明列含义、单位、误差条、归一化，并登记到 `data_manifest.csv` 与 `figure_manifest.csv`。
11. 科学等价：路径、读写、环境修复属常规；算法、阈值、样本选取、归一化、单位、模型参数、统计口径、图意的改动必须单独 PR 并标 `needs-user`。
12. 不得把未运行的测试写成通过；验证报告逐项标 PASS / FAIL / EXCEPTION / NOT VERIFIED。

## 命令
`make gates`、`make figures-fast`、`make all`、`make validate`（`-full`）、`make graph`、`make paper`、`python tools/import_legacy.py <目录>`。

## 旧项目导入（`import` issue）
按 `docs/REPRODUCIBILITY_STANDARD_cn.md`：
1. 盘点 PR：运行 `tools/import_legacy.py` 生成清单、迁移映射草案、基准报告；尽量在原环境跑一次基准。不移动任何文件。
2. 负责人审阅迁移映射（`needs-user`）；删除、改写数据集、科学改动须明确批准。
3. 迁移 PR：按字节复制、追加 `file_migration_map.csv`、登记原始数据、修路径、补两份清单、写 `CHANGELOG.md`。
4. 原始数据中的中文冲突不得悄悄修改，登记到 `audit/EXCEPTIONS.yaml` 由负责人决定。
5. `make validate-full` 与基准在事先规定的容差内一致才算完成。
