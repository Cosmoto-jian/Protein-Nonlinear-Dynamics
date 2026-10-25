# AI for Science 研究项目模板（v4 精简版）

一个研究项目 = 一个仓库 = 一个 `main`。用 **Use this template** 新建。

项目自己跑闭环：`make next` 读取仓库状态，给出唯一一件最该做的事；智能体在分支上完成、开 PR，5 道门禁决定能否合并。

```
make next → 分支 → 做任务 → PR → make gates + make validate → 合并 → make next …
```

三个文件是唯一事实来源，其余全部由它们生成：

| 文件 | 内容 |
|---|---|
| `STUDY.yaml` | 研究问题、目标、循环预算（仅负责人可改） |
| `pipeline.yaml` | 所有正式步骤的命令、输入、输出、参数；`pipeline.lock` 记哈希；`data_manifest.csv`、`figure_manifest.csv`、`graph.json` 自动生成 |
| `research/claims.yaml` | 只追加的结论账本：supported / refuted / inconclusive / dead-end |

## 本研究
机械敏感通道 Cα 桁架在保守膜张力下的几何非线性力学：张力响应如何偏离其线性化（刚化、转向、失稳），以显式 VFIFE 与带约束的 Newton 法互相验证，并用 Sylvester 惯性定理认证稳定性。

| 内容 | 位置 |
|---|---|
| 结构文件（OPM、RCSB）与旧版参考路径 | `data/raw/`（`MANIFEST.yaml`） |
| 分析代码与求解器 | `src/`（见 `src/README.md`） |
| 张力路径、校核、汇总 | `data/derived/`（流水线输出） |
| 图 1-7、A.1、A.2 | `plot/figN.py` -> `figure_data/figN/` -> `results/figures/` |
| 论文（elsarticle） | `writing/tex/main.tex`；数字与表格在 `writing/tex/gen/` |

完整链（`make all`）在 10 核工作站上约需一到两天，主要耗时在 Piezo1 路径、延拓和重连网络零模型；快速链（`make figures-fast`）只需数秒。论文用 `make paper` 编译。

## 常用命令
```bash
make next           # 下一件事
make gates          # 5 道门禁（与 CI 相同）
make status         # 哪些步骤过期
make all            # 重跑过期步骤：raw → derived → runs → figure_data → 图
make figures-fast   # 只从 figure_data/ 重画
make validate       # 干净副本验证
```

## 环境说明
- `pypardiso`（MKL PARDISO）可选，仅 x86_64；有它时 `src/kkt.py` 用一次稀疏 LDL^T 分解完成 Newton 求解、惯性计数和特征值；没有时（或 `PND_NO_PARDISO=1`）走 scipy 路径（结果相同，慢得多）。
- 线程数可复现性：`src/kkt.py` 在加载 MKL 前设置 `MKL_CBWR=AUTO,STRICT`（环境变量中已有的值优先），`tools/prun2.py` 对每一步也设置它，使 PARDISO 结果与 `MKL_NUM_THREADS` 无关（不设时差异约 1e-13 相对量级）。
- 双 VM 运行：主 VM 上 `python tools/prun2.py`（环境变量 `PRUN2_WORKER`、`PRUN2_TEAM`、`FREESTYLE_API_KEY`）；API key 只通过环境变量传入，不留在 VM 上。
- 单元测试：`python tests/test_kkt.py`；无 pypardiso 时跳过 PARDISO 测试。

## 语言规则
代码、配置、数据、文件名和英文文档不含中文。中文只在 `*_cn.md`，且必须有同名纯英文文件。

目录说明见 `README.md`；智能体规则见 `AGENTS_cn.md`。
