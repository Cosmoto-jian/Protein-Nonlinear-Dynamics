# AI for Science 研究项目模板（v3.3）

一个研究项目 = 一个仓库 = 一个 `main`。用 **Use this template** 新建项目，之后独立进化。

```
issue → fix/I-xxx → 先写红灯检查 → 修复 → PR → make gates 全绿 → 合并 main → 重建下游 → 复查 → 关闭
```

交付标准：把仓库复制到干净位置，只按本文档配置，就能在不访问任何其他目录的情况下重建图和核心结果（见 `docs/REPRODUCIBILITY_STANDARD_cn.md`）。

## 快速开始
```bash
pip install -r requirements.txt
make gates          # 全部 9 道门禁（与 CI 相同）
make figures-fast   # figure_data/ → 图 + 描述
make all            # data/raw → data/derived → runs → figure_data → 图
make validate       # 干净副本验证 → results/logs/validation_report.md
make graph          # 溯源图 graph.json
```

## 语言规则
代码、配置、数据、文件名和英文文档一律不含中文。中文只能出现在 `*_cn.md`，且必须有同名纯英文文件（本文件对应 `README.md`）。

目录说明见 `README.md`；智能体规则见 `AGENTS_cn.md`。
