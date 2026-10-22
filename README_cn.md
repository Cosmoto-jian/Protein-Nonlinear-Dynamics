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

## 常用命令
```bash
make next           # 下一件事
make gates          # 5 道门禁（与 CI 相同）
make status         # 哪些步骤过期
make all            # 重跑过期步骤：raw → derived → runs → figure_data → 图
make figures-fast   # 只从 figure_data/ 重画
make validate       # 干净副本验证
```

## 语言规则
代码、配置、数据、文件名和英文文档不含中文。中文只在 `*_cn.md`，且必须有同名纯英文文件。

目录说明见 `README.md`；智能体规则见 `AGENTS_cn.md`。
