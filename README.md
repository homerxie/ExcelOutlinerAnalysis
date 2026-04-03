# Excel Data Analysis

这是一个面向 Excel/CSV 表格数据的模板驱动异常分析项目骨架，目标是服务于“按业务模板自动聚类 + 异常检测 + 历史数据持续对比”的场景，适用于 macOS 和 Windows。

当前版本已经补上了一条更贴近真实芯片可靠性表的主流程：

- 支持多表头 `xlsx` 输入
- 支持模板文件使用 `json` 或“人类更易编辑”的 `xlsx`
- 支持从 `recordName` 这类复合字段拆出 `SampleID / node / repeat`
- 支持按链路、测试条件、重复次数重排结果列
- 一次导出 `Sorted / deviation-zscore / deviation-golden / outliners / Outliner Summary`
- 支持把 golden、阈值、node 顺序、outlier 判定标准放进模板 JSON

## 目标能力

- 支持 `csv` 和 `xlsx`
- 支持多行表头和列乱序的 `xlsx`
- 横向模板定义
  - 哪些列属于同一类数据并应合并分析
  - 哪些列要分别分析但在结果中一起呈现
- 纵向模板定义
  - 哪些列代表样品编号、可靠性节点、重复次序，以及更多层级维度
  - 哪些字段需要从同一个 `recordName` 拆出来
- 支持历史数据仓库存档
  - 后续导入新的可靠性节点后，可以与历史数据联动分析
- 支持两类异常策略
  - `golden reference`
  - `modified z-score`
- 支持面向芯片可靠性报告的多 sheet Excel 导出

## 为什么先做 Python 核心

你的问题核心是“复杂业务模板 + 统计分析 + 持久化历史数据”，这部分比 UI 更重要。第一版先把核心分析引擎稳定下来，后续可以在上面接：

- `PySide6` 桌面 UI，打包成 macOS/Windows 应用
- 或 Web UI

当前仓库已经补了一个可直接测试的 `PySide6` GUI，后续也可以在这个基础上继续大改界面。

## 跨平台与打包

当前代码已经按 `macOS + Windows` 两端可运行来整理：

- 运行时路径改成 `pathlib`
- GUI 默认数据库目录使用用户目录下的可写位置，而不是仓库当前目录
- GUI 默认模板改成包内自带模板，因此 PyInstaller 打包后仍可直接启动
- 提供了独立的 PyInstaller spec：
  - `excel-data-analysis-gui.spec`
  - `excel-data-analysis-cli.spec`

注意：

- `PyInstaller` 需要在目标平台各自打包，不能在 macOS 上直接产出 Windows 可执行文件，反之亦然
- 也就是说：
  - macOS 包请在 macOS 上构建
  - Windows 包请在 Windows 上构建

## 核心概念

### 1. 行维度 `row_dimensions`

用于告诉系统，每一行的前几列文本里，哪些列表示什么业务含义。

现在 `row_dimensions` 支持一个维度挂多个 `sources`。每个 source 可以单独配置：

- `column`
- `split_position`
- `split_delimiters`
- `skip_empty_parts`

这样可以实现：

- 同一个维度值从多个原始列取值
- 每个原始列先按不同 delimiter 拆分
- 再把多个 source 的结果按顺序重组成同一个维度

示例：

- `sample_id`：样品编号
- `reliability_node`：可靠性节点/轮次
- `repeat_id`：同一样品同一节点下的重复测试次数
- `site_id`：第四层维度，例如 site、链路、腔体等

### 2. 分析组 `analysis_groups`

用于描述横向测试项目该如何分析。

- `pooled_columns`
  - 多列本质上是同一逻辑测项，比如同一电阻在固定条件下重复测 3 次
  - 这几列会被当成同一类数据做分析
- `per_column`
  - 多列需要分别分析，比如电阻、电流、电压、电容
  - 但它们可以通过 `presentation_group` 被摆在一起展示

### 3. Golden Reference

从某个基准轮次或基准样品生成长期可复用的 golden 文件。

常见做法：

- 用 `sample_id` 作为 reference key
- 用 `reliability_node=T0` 作为 baseline filter
- 得到“每个样品自己的基准范围”

阈值支持：

- 相对偏差，例如 `20%`
- 标准差倍数，例如 `3 sigma`
- 混合模式，同时收紧边界

### 4. Modified Z-Score

不使用 golden reference，直接在某个大池子内找异常值。适合：

- 没有参考轮次时
- 想先做总体异常扫描时

## 快速开始

### 1. 安装

```bash
pip3 install -e .
```

如果你只是先在仓库里直接试跑，还没做安装，也可以使用开发态方式：

```bash
PYTHONPATH=src python3 -m excel_data_analysis.cli --help
```

### 1.1 启动 GUI

安装依赖后可以直接运行：

```bash
source .venv/bin/activate
excel-data-analysis-gui
```

打包桌面版前可先安装构建依赖：

```bash
pip install -e ".[build]"
```

### 1.2 用 PyInstaller 打包

GUI 桌面版：

```bash
pyinstaller excel-data-analysis-gui.spec
```

CLI 独立可执行版：

```bash
pyinstaller excel-data-analysis-cli.spec
```

产物默认会出现在：

- `dist/ExcelDataAnalysis/` 或 `dist/ExcelDataAnalysis.app`
- `dist/excel-data-analysis`

打包后的 GUI 默认行为：

- 内置一份 JSON 模板
- 默认数据库目录位于用户可写目录
- 默认导出目录位于用户 `Documents/ExcelDataAnalysis/exports`

如果还没做 editable install，也可以：

```bash
source .venv/bin/activate
PYTHONPATH=src python3 -m excel_data_analysis.gui.app
```

### 1.3 Windows 一键安装

如果你要在 Windows 上快速试运行，直接在项目根目录双击：

```bat
setup_windows.bat
```

它会自动：

- 检查是否已有 Python 3.10+
- 如果没有，先尝试自动安装 Python
- 在当前项目目录下创建 `.venv`
- 安装 `requirements.txt` 中的依赖

安装完成后可用下面命令启动 GUI：

```bat
.venv\Scripts\python -m excel_data_analysis.gui.app
```

如果后面还要测试 PyInstaller 打包，再额外执行：

```bat
.venv\Scripts\python -m pip install -r requirements-build.txt
```

### 2. 导入数据到本地历史仓库

这里的 `--storage` 就是一套独立数据库的目录。  
如果你要维护多套数据库，直接使用不同的目录即可，例如 `.eda_store/project_a`、`.eda_store/project_b`。

```bash
excel-data-analysis import-data \
  --template examples/chip_reliability_template.json \
  --input /path/to/data.xlsx \
  --storage .eda_store/project_a
```

模板路径也可以直接换成 `examples/chip_reliability_template.xlsx`。

如果导入文件和当前数据库里已有数据出现同样的 sample/node/site... 键：

- `--conflict-mode error`
  - 默认模式，先报冲突，不写入
- `--conflict-mode replace`
  - 删掉当前数据库里同键的旧数据，再导入新数据
- `--conflict-mode append`
  - 保留旧数据，并把新数据的 `repeat_id` 继续往后累加

```bash
excel-data-analysis import-data \
  --template examples/chip_reliability_template.json \
  --input /path/to/data.xlsx \
  --storage .eda_store/project_a \
  --conflict-mode append
```

导入前也可以先预览冲突：

```bash
excel-data-analysis preview-import \
  --template examples/chip_reliability_template.json \
  --input /path/to/data.xlsx \
  --storage .eda_store/project_a
```

查看当前数据库里已经有哪些数据：

```bash
excel-data-analysis show-storage \
  --template examples/chip_reliability_template.json \
  --storage .eda_store/project_a \
  --limit 200
```

### 3. 基于某个节点构建 golden

下面例子表示：

- 用 `sample_id` 作为 golden key
- 只使用 `reliability_node=T0` 的数据建 golden
- 正常范围使用 `20%` 相对偏差

```bash
excel-data-analysis build-golden \
  --storage .eda_store \
  --name chip_t0_golden \
  --reference-dims sample_id \
  --filter reliability_node=T0 \
  --center-method mean \
  --threshold-mode relative \
  --relative-limit 0.2
```

`--center-method` 当前支持：

- `mean`
- `median`

### 4. 查看数据库导入历史

```bash
excel-data-analysis show-imports \
  --storage .eda_store
```

### 5. 直接从数据库生成真实芯片报表

整库导出：

```bash
excel-data-analysis generate-report \
  --template examples/chip_reliability_template.json \
  --storage .eda_store \
  --output examples/sample_chip_data_real_result.xlsx
```

只导出某几个 sample / node：

```bash
excel-data-analysis generate-report \
  --template examples/chip_reliability_template.json \
  --storage .eda_store \
  --sample-ids S001,S002 \
  --nodes T0,T1 \
  --output examples/sample_chip_data_real_result.xlsx
```

### 6. 直接生成真实芯片报表

如果你的输入是像 `examples/sample_chip_data_real.xlsx` 这样带多行表头、列顺序可能打乱、`recordName` 里还塞了多个维度的真实表，直接用：

```bash
excel-data-analysis generate-report \
  --template examples/chip_reliability_template.json \
  --input examples/sample_chip_data_real.xlsx \
  --output examples/sample_chip_data_real_result.xlsx \
  --if-exists timestamp \
  --outlier-fail-mode zscore_or_golden
```

这个命令会生成 5 个 sheet：

- `Sorted`
  - 把列按链路 / 测试条件 / 重复次数重排
  - 把 `recordName` 拆成可读的行维度
  - 把 golden 值直接写在表头里
- `deviation-zscore`
  - 写出全部测试点的 z-score
  - 每列显示对应 threshold，fail 标红
- `deviation-golden`
  - 写出全部测试点相对 golden 的偏差
  - 每列显示对应 threshold，fail 标红
- `outliners`
  - 按 sample 分块，只保留存在异常链路的完整数据
  - 同时展示原值、z-score、golden deviation、Pass/Fail
- `Outliner Summary`
  - 汇总哪些 sample / 哪条链路 / 哪个 node 开始异常
  - 同时输出模板里配置的 node 顺序供参考

报表里：

- `deviation-zscore` 和 `deviation-golden` 都会始终输出
- 两类偏差各自超 threshold 时都会标红
- `outliners` 里的 `Pass/Fail` 可以单独选择判定标准：
  - `modified_z_score`
  - `golden_deviation`
  - `zscore_and_golden`
  - `zscore_or_golden`

所有会写文件的 CLI 命令都支持：

- `--if-exists error`
- `--if-exists overwrite`
- `--if-exists timestamp`

如果你只想先看报表里会被判成 fail 的测试点，也可以用：

```bash
excel-data-analysis report-failures \
  --template examples/chip_reliability_template.json \
  --input examples/sample_chip_data_real.xlsx
```

## Excel 模板与 JSON 模板互转

如果你觉得 JSON 模板太冗长，现在可以直接使用 Excel 模板编辑。程序内部会把它解析成同一套 `TemplateConfig`，所以导入、建 golden、分析、报表都能直接吃 `xlsx` 模板。

当前仓库自带两个等价示例：

- `examples/chip_reliability_template.json`
- `examples/chip_reliability_template.xlsx`

### 校验模板

```bash
excel-data-analysis validate-template \
  --input examples/chip_reliability_template.xlsx
```

### JSON 转 Excel

```bash
excel-data-analysis template-to-xlsx \
  --input examples/chip_reliability_template.json \
  --output examples/chip_reliability_template.xlsx
```

### Excel 转 JSON

```bash
excel-data-analysis template-to-json \
  --input examples/chip_reliability_template.xlsx \
  --output /tmp/chip_reliability_template.json
```

Excel 模板当前包含这些 sheet：

- `template_info`
- `row_dimensions`
- `analysis_groups`
- `golden_values`
- `zscore_thresholds`
- `golden_deviation_thresholds`
- `README`

新的 Excel 模板会尽量避免单元格内换行：

- `row_dimensions` 会写成长表，每个 source 单独占一行，并使用 `delimiter_1 / delimiter_2 / ...`
- `analysis_groups` 会写成长表，每个 `column_name` 单独占一行，方便做漏项和唯一性校验
- `node_orders` 会横向展开成多列，例如 `node_1 / node_2 / ...`

如果同一套模板里可能出现多种节点路径，例如：

- `T0 -> T1 -> T2`
- `T0 -> T1 -> T3 -> T4`

可以改用：

```json
"report": {
  "node_orders": [
    ["T0", "T1", "T2"],
    ["T0", "T1", "T3", "T4"]
  ]
}
```

程序会为每个 sample 自动匹配最合适的节点顺序，用于：

- 报表行排序
- `outliners` 中节点前后关系判断
- `Outliner Summary` 中“从哪个 node 开始失效”的排序与展示

Excel 模板里：

- `row_dimensions` sheet：一行表示一个 source
- `node_orders` sheet：一行表示一条 sequence，每个 node 单独占一个单元格

## 目录结构

```text
src/excel_data_analysis/
  analyzer.py        # 统计分析核心
  cli.py             # 命令行入口
  io.py              # Excel/CSV 读取与数值转换
  models.py          # 领域模型
  repository.py      # 本地历史仓库
  template.py        # 模板加载与校验
  exporters.py       # JSON / Excel 导出
  service.py         # GUI/CLI 共用业务入口
  gui/app.py         # PySide6 GUI 主程序
  gui/main_window.ui # Qt Designer UI 文件
  gui/ui_main_window.py
examples/
  chip_reliability_template.json
  chip_reliability_template.xlsx
```

## GUI 开发约定

GUI 相关文件建议按下面的职责分层：

- [main_window.ui](/Users/xiezihong/Documents/Programming/ExcelDataAnalysis/src/excel_data_analysis/gui/main_window.ui)
  - Qt Designer 的布局真源
- [ui_main_window.py](/Users/xiezihong/Documents/Programming/ExcelDataAnalysis/src/excel_data_analysis/gui/ui_main_window.py)
  - 由 `.ui` 自动生成
  - 不建议手改
- [app.py](/Users/xiezihong/Documents/Programming/ExcelDataAnalysis/src/excel_data_analysis/gui/app.py)
  - 放事件绑定、状态切换、业务逻辑、弹窗、导入导出等 `.ui` 不适合表达的行为

重新生成 `ui_main_window.py` 的命令：

```bash
./.venv/bin/pyside6-uic \
  src/excel_data_analysis/gui/main_window.ui \
  -o src/excel_data_analysis/gui/ui_main_window.py
```

## 后续推荐路线

第一阶段：

- 先拿 1~2 份真实表格把模板跑通
- 校准“横向聚类”和“纵向维度”是否足够表达你的业务
- 把 `recordName` 拆解规则、golden 值、threshold、node 顺序固化到模板

第二阶段：

- 增加结果导出 Excel
- 增加异常汇总页
- 增加 golden 文件版本管理

第三阶段：

- 接入 `PySide6` 图形界面
- 打包成 macOS/Windows 桌面应用

## 注意

- 当前版本是“可扩展核心骨架”，重点是把模板抽象、历史仓库和分析流程固定下来
- `xlsx` 读取依赖 `openpyxl`
- GUI 现在支持模板校验、`json/xlsx` 双向转换，以及直接加载 Excel 模板
- `report.node_order` 是单条旧写法；`report.node_orders` 是支持多条 sequence 的新写法，二者兼容
- 真实芯片报表导出依赖模板里的 `report` 配置
- `report.outlier_fail_method` 目前支持 `modified_z_score` 和 `golden_deviation`
- `report.outlier_chain_fail_rule` 目前支持 `any_fail` 和 `all_fail`
- 如果后续你的数据量非常大，可以把仓库存储从 `jsonl` 升级成 `SQLite`
