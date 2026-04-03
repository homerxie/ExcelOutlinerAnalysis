# Template Help

[toc]



这份文档说明当前程序支持的 template 格式、每个字段的含义、可选值、Excel 模板各个 sheet 的写法，以及常见校验规则。

当前 template 支持两种文件格式：

- `json`
- `xlsx`

程序内部都会先把它们解析成同一套 `TemplateConfig`。  
对应实现主要在：

- [template.py](/Users/xiezihong/Documents/Programming/ExcelDataAnalysis/src/excel_data_analysis/template.py)
- [models.py](/Users/xiezihong/Documents/Programming/ExcelDataAnalysis/src/excel_data_analysis/models.py)
- [io.py](/Users/xiezihong/Documents/Programming/ExcelDataAnalysis/src/excel_data_analysis/io.py)

示例文件：

- [chip_reliability_template.json](/Users/xiezihong/Documents/Programming/ExcelDataAnalysis/examples/chip_reliability_template.json)
- [chip_reliability_template.xlsx](/Users/xiezihong/Documents/Programming/ExcelDataAnalysis/examples/chip_reliability_template.xlsx)

## 1. 顶层结构

JSON template 的顶层字段如下：

```json
{
  "name": "chip_reliability_template",
  "header_row": 0,
  "measurement_header_row": 0,
  "row_header_row": 4,
  "unit_row": 3,
  "data_start_row": 5,
  "row_dimensions": [],
  "analysis_groups": [],
  "report": {}
}
```

各字段说明：

- `name`
  - 类型：`string`
  - 必填
  - 模板名称，仅作为标识使用

- `header_row`
  - 类型：`int`
  - 可选，默认 `0`
  - 基础表头行号，零基准
  - 如果没有单独指定 `measurement_header_row`，它会作为测量列表头行

- `measurement_header_row`
  - 类型：`int`
  - 可选
  - 测量列表头所在行，零基准
  - 如果省略，默认等于 `header_row`

- `row_header_row`
  - 类型：`int`
  - 可选
  - 行维度列名所在行，零基准
  - 如果省略，默认等于 `measurement_header_row`

- `unit_row`
  - 类型：`int`
  - 可选
  - 单位行所在位置，零基准

- `data_start_row`
  - 类型：`int`
  - 可选
  - 数据开始行，零基准
  - 如果省略，程序会自动取表头/单位行之后的下一行

- `row_dimensions`
  - 类型：`list`
  - 必填
  - 描述一行数据的业务维度怎么提取

- `analysis_groups`
  - 类型：`list`
  - 必填
  - 描述横向测试列如何分组与分析

- `report`
  - 类型：`object`
  - 可选，但真实芯片报表一般都会配置
  - 控制 golden、threshold、node 顺序、outlier 判定规则

## 2. `row_dimensions`

`row_dimensions` 用来定义每一行的维度信息，例如：

- `sample_id`
- `reliability_node`
- `repeat_id`
- `site_id`
- `temp`

当前结构不是旧版的 `columns + split_position`，而是：

```json
{
  "name": "sample_id",
  "display_name": "SampleID",
  "optional": false,
  "default_value": null,
  "sources": [
    {
      "column": "recordName",
      "split_delimiters": ["_", "｜"],
      "split_position": 0,
      "skip_empty_parts": false
    }
  ]
}
```

### 2.1 `row_dimension` 字段说明

- `name`
  - 类型：`string`
  - 必填
  - 维度内部名称
  - 后续会作为 `dimensions[name]` 的 key 使用
  - 不能重复

- `display_name`
  - 类型：`string`
  - 可选
  - 报表里展示的标题名称
  - 如果省略，界面/报表会退回使用 `name`

- `optional`
  - 类型：`bool`
  - 可选，默认 `false`
  - 如果该维度提取不到值：
    - `true`：允许缺失
    - `false`：整行数据会被视为无效并跳过

- `default_value`
  - 类型：`string`
  - 可选
  - 当所有 source 都提取不到值时的回填值
  - 常见用法：`repeat_id` 默认写 `"1"`

- `sources`
  - 类型：`list`
  - 必填
  - 一个维度可以有多个 source
  - 程序会按 source 顺序提取内容
  - 多个 source 的结果会用 `|` 拼接成最终维度值

### 2.2 `row_dimension.sources[]` 字段说明

每个 source 都有自己的提取规则：

- `column`
  - 类型：`string`
  - 必填
  - 从输入表的哪一列取原始文本

- `split_delimiters`
  - 类型：`list[string]`
  - 可选
  - 一个 source 可以配置多个 delimiter
  - 例如：`["_", "｜"]`
  - 程序会按“任一 delimiter 都可切分”的规则拆开文本
  - 这是普通文本切分，不是正则表达式

- `split_position`
  - 类型：`int`
  - 可选
  - 表示 split 之后取第几个片段，零基准
  - 例如：
    - `recordName = "S001_T1_2"`
    - `split_delimiters = ["_"]`
    - `split_position = 1`
    - 结果就是 `"T1"`
  - 如果配置了 `split_position`，必须同时配置 `split_delimiters`

- `skip_empty_parts`
  - 类型：`bool`
  - 可选，默认 `false`
  - 对连续分隔符导致的空字符串片段是否忽略
  - 例如 `A__B` 按 `_` 切分时：
    - `false`：结果是 `["A", "", "B"]`
    - `true`：结果是 `["A", "B"]`

### 2.3 `row_dimensions` 的实际行为

程序提取维度时的规则：

1. 按 `row_dimensions` 顺序处理每个维度
2. 对当前维度，按 `sources` 顺序依次提取
3. 每个 source：
   - 如果没配 `split_position`：直接取整格文本
   - 如果配了 `split_position`：先按 `split_delimiters` 切分，再取指定位置
4. 把所有成功提取的 source 结果用 `|` 拼起来
5. 如果一个维度所有 source 都没拿到值：
   - 有 `default_value` 就用默认值
   - 没默认值但 `optional=true` 就跳过该维度
   - 否则整行数据无效

### 2.4 `row_dimensions` 的典型例子

#### 例 1：从一个列里拆出 sample/node/repeat

```json
{
  "name": "sample_id",
  "display_name": "SampleID",
  "sources": [
    {
      "column": "recordName",
      "split_delimiters": ["_", "｜"],
      "split_position": 0
    }
  ]
}
```

#### 例 2：一个维度从多个原始列重组

```json
{
  "name": "location",
  "display_name": "Location",
  "sources": [
    {
      "column": "Line"
    },
    {
      "column": "Site"
    }
  ]
}
```

如果 `Line=A`，`Site=03`，最终维度值会是：

```text
A|03
```

#### 例 3：多个 source 各自 split 后重组

```json
{
  "name": "device_key",
  "display_name": "DeviceKey",
  "sources": [
    {
      "column": "recordA",
      "split_delimiters": ["_", "｜"],
      "split_position": 0
    },
    {
      "column": "recordB",
      "split_delimiters": ["-", ":"],
      "split_position": 1
    }
  ]
}
```

## 3. `analysis_groups`

`analysis_groups` 用来定义横向测试列如何归类。

结构示例：

```json
{
  "id": "link1_resistance",
  "display_name": "Link1 Resistance",
  "columns": [
    "R_Link1_1V_1",
    "R_Link1__1V_2",
    "R_Link1_1V_3"
  ],
  "analysis_mode": "pooled_columns",
  "presentation_group": "Link1",
  "unit": "Ohm"
}
```

### 3.1 字段说明

- `id`
  - 类型：`string`
  - 必填
  - analysis group 的唯一标识
  - 不能重复

- `display_name`
  - 类型：`string`
  - 可选
  - 展示名称
  - 如果省略，默认使用 `id`

- `columns`
  - 类型：`list[string]`
  - 必填
  - 属于这个 group 的原始输入列名
  - 同一个 raw column 不能出现在多个 group 里

- `analysis_mode`
  - 类型：`string`
  - 必填
  - 允许值：
    - `pooled_columns`
    - `per_column`

- `presentation_group`
  - 类型：`string`
  - 可选
  - 主要影响报表展示分组，例如 `Link1`、`Link2`

- `unit`
  - 类型：`string`
  - 可选
  - 该组默认单位
  - 如果输入表 unit 行里已经有单位，会优先用表里的单位

### 3.2 `analysis_mode` 说明

- `pooled_columns`
  - 多列被视为同一个逻辑测项
  - 逻辑 metric key 使用 `group.id`
  - 常见于同条件重复测量

- `per_column`
  - 每个 raw column 各自作为一个独立逻辑测项
  - 逻辑 metric key 使用 `group.id::raw_column`
  - 常见于同链路下不同电压/电流/模式的独立项目

### 3.3 `analysis_groups` 的 Excel 写法

Excel 模板中，`analysis_groups` 使用长表模式：

- 一行代表一个 `column_name`
- 所有 raw column 都集中在同一列，方便查漏

表头如下：

- `id`
- `display_name`
- `analysis_mode`
- `presentation_group`
- `unit`
- `column_order`
- `column_name`

例子：

```text
link1_resistance | Link1 Resistance | pooled_columns | Link1 | Ohm | 1 | R_Link1_1V_1
link1_resistance | Link1 Resistance | pooled_columns | Link1 | Ohm | 2 | R_Link1__1V_2
link1_resistance | Link1 Resistance | pooled_columns | Link1 | Ohm | 3 | R_Link1_1V_3
```

`column_order` 用来保留原来的列顺序。

## 4. `report`

`report` 主要控制真实芯片多 sheet 报表的行为。

结构示例：

```json
"report": {
  "golden_values": {},
  "zscore_thresholds": {
    "default": 3.5
  },
  "golden_deviation_thresholds": {
    "default": 0.05
  },
  "outlier_ratio_stats": [],
  "node_order": ["T0", "T1", "T2"],
  "outlier_fail_method": "golden_deviation",
  "outlier_chain_fail_rule": "any_fail"
}
```

### 4.1 `golden_values`

- 类型：`dict[string, number]`
- 可选
- 用于直接指定 golden 值

key 支持的匹配优先顺序是：

1. `logical_metric`
2. `raw_column`
3. `group_id`
4. `chain_name`

其中最常用的是：

- `group_id`
  - 例如 `link1_resistance`
- `group_id::raw_column`
  - 例如 `link1_current::I_Link1_1p8V`

例子：

```json
"golden_values": {
  "link1_resistance": 99,
  "link1_current::I_Link1_1p8V": 9.6
}
```

### 4.2 `zscore_thresholds`

- 类型：`object` 或 `number`
- 可选

如果直接写数字：

```json
"zscore_thresholds": 3.5
```

等价于：

```json
"zscore_thresholds": {
  "default": 3.5
}
```

完整写法：

```json
"zscore_thresholds": {
  "default": 3.5,
  "overrides": {
    "link1_resistance": 4.0,
    "I_Link1_1p8V": 2.5
  }
}
```

override key 的匹配优先顺序是：

1. `logical_metric`
2. `raw_column`
3. `group_id`
4. `chain_name`

### 4.3 `golden_deviation_thresholds`

- 类型：`object` 或 `number`
- 可选
- 写法和 `zscore_thresholds` 一样
- 默认值通常是相对偏差，例如 `0.05`

例子：

```json
"golden_deviation_thresholds": {
  "default": 0.05,
  "overrides": {
    "link2_capacitance": 0.1
  }
}
```

### 4.4 `node_order` 与 `node_orders`

这两个字段用来描述 node 的先后顺序。

- `node_order`
  - 类型：`list[string]`
  - 旧的单条顺序写法

- `node_orders`
  - 类型：`list[list[string]]`
  - 新的多条顺序写法
  - 更推荐使用

单条例子：

```json
"node_order": ["T0", "T1", "T2"]
```

多条例子：

```json
"node_orders": [
  ["T0", "T1", "T2"],
  ["T0", "T1", "T3", "T4"]
]
```

程序会按每个 sample 实际出现的 node 集合，自动匹配最合适的顺序，用于：

- 报表行排序
- outlier 发生先后判断
- summary 里“从哪个 node 开始失效”的展示

#### node 顺序一致性校验

多条 `node_orders` 允许存在，但公共节点之间的相对顺序不能冲突。

允许：

```json
[
  ["T0", "T1", "T2"],
  ["T0", "T1", "T3", "T4"]
]
```

不允许：

```json
[
  ["T0", "T1", "T2"],
  ["T2", "T1", "T0"]
]
```

因为第二条把公共节点顺序反过来了。

### 4.5 `outlier_ratio_stats`

- 类型：`list[object]`
- 可选
- 用于在 `Outliner Summary` 里增加“outlier 占比”统计表

每一项都表示一类统计规则。程序会在当前分析范围内：

- 先按 `group_by_dimension` 分组
- 再统计该组里唯一 sample 的总数
- 再统计满足条件的 outlier sample 数
- 最后得到 `outlier_ratio = outlier_sample_count / total_sample_count`

当前结构如下：

```json
{
  "id": "new_ratio_by_node_all",
  "display_name": "New Outlier Ratio By Node",
  "group_by_dimension": "reliability_node",
  "numerator": "new_outlier_samples",
  "chains": [],
  "raw_columns": [],
  "logical_metrics": []
}
```

字段说明：

- `id`
  - 类型：`string`
  - 必填
  - 该统计项的唯一标识

- `display_name`
  - 类型：`string`
  - 可选
  - 在 Excel / GUI 里显示的名称

- `group_by_dimension`
  - 类型：`string`
  - 必填
  - 必须是一个已定义的 `row_dimensions.name`
  - 最常用的是 `reliability_node`
  - 也可以是 `site_id`、`temp` 等其它行维度

- `numerator`
  - 类型：`string`
  - 必填
  - 允许值：
    - `new_outlier_samples`
    - `outlier_samples`

含义：

- `new_outlier_samples`
  - 只统计该组里状态为 `New` 的 outlier sample 数
  - 适合看“相对于前驱节点新增失效”的比例

- `outlier_samples`
  - 统计该组里所有 outlier sample 数，不区分 `New / Existed`
  - 适合看该组当前总 outlier 覆盖率

- `chains`
  - 类型：`list[string]`
  - 可选
  - 只统计指定 chain
  - 例如：`["Link4"]`

- `raw_columns`
  - 类型：`list[string]`
  - 可选
  - 只统计命中特定原始测试列的 outlier
  - 例如：`["V_Link1_1p8V"]`

- `logical_metrics`
  - 类型：`list[string]`
  - 可选
  - 只统计命中特定 logical metric 的 outlier
  - 例如：`["link1_voltage::V_Link1_1p8V"]`

过滤规则：

- `chains`、`raw_columns`、`logical_metrics` 可以同时配置
- 如果同时配置多个过滤器，程序要求该 outlier 事件至少命中每一类过滤器中的一项
- 如果都不配置，表示“所有 outlier 都参与统计”

典型例子：

#### 例 1：统计每个 node 的新增 outlier 比例

```json
"outlier_ratio_stats": [
  {
    "id": "new_ratio_by_node_all",
    "display_name": "New Outlier Ratio By Node",
    "group_by_dimension": "reliability_node",
    "numerator": "new_outlier_samples"
  }
]
```

含义：

- 以 `reliability_node` 分组
- 分母：该 node 下 sample 总数
- 分子：该 node 下 `status = New` 的 outlier sample 数

#### 例 2：只统计 Link4 的总 outlier 比例

```json
"outlier_ratio_stats": [
  {
    "id": "total_ratio_by_node_link4",
    "display_name": "Total Outlier Ratio By Node (Link4)",
    "group_by_dimension": "reliability_node",
    "numerator": "outlier_samples",
    "chains": ["Link4"]
  }
]
```

#### 例 3：只统计某个测试列的总 outlier 比例

```json
"outlier_ratio_stats": [
  {
    "id": "total_ratio_by_node_v_link1_1p8v",
    "display_name": "Total Outlier Ratio By Node (V_Link1_1p8V)",
    "group_by_dimension": "reliability_node",
    "numerator": "outlier_samples",
    "raw_columns": ["V_Link1_1p8V"]
  }
]
```

### 4.6 `outlier_fail_method`

- 类型：`string`
- 可选
- 允许值：
  - `modified_z_score`
  - `golden_deviation`
  - `zscore_and_golden`
  - `zscore_or_golden`

含义：

- `modified_z_score`
  - `outliners` / `summary` 里以 zscore 判 fail

- `golden_deviation`
  - `outliners` / `summary` 里以 golden 偏差判 fail

- `zscore_and_golden`
  - zscore 和 golden 偏差都超 threshold 才判 fail

- `zscore_or_golden`
  - zscore 和 golden 偏差任意一个超 threshold 就判 fail

注意：

- GUI 中如果 Analysis Mode 和这个值不一致，程序会提示是否同步刷新 template

### 4.7 `outlier_chain_fail_rule`

- 类型：`string`
- 可选
- 允许值：
  - `any_fail`
  - `all_fail`

含义：

- `any_fail`
  - 一个 chain 里只要任意测试项 fail，就认为这个 chain fail

- `all_fail`
  - 一个 chain 里所有测试项都 fail，才认为这个 chain fail

## 5. Excel Template 结构

Excel 模板包含这些 sheet：

- `template_info`
- `row_dimensions`
- `analysis_groups`
- `node_orders`
- `golden_values`
- `zscore_thresholds`
- `golden_deviation_thresholds`
- `outlier_ratio_stats`
- `README`

### 5.1 `template_info`

一行一个字段，表头固定为：

- `field`
- `value`
- `notes`

常见 field：

- `name`
- `header_row`
- `measurement_header_row`
- `row_header_row`
- `unit_row`
- `data_start_row`
- `node_order`
  - 在 Excel 里已经废弃，仅保留提示
- `outlier_fail_method`
- `outlier_chain_fail_rule`

### 5.2 `row_dimensions`

一行表示一个 source。表头：

- `name`
- `display_name`
- `optional`
- `default_value`
- `source_order`
- `source_order`
  - 类型：`int`
  - Excel 模板专用
  - 用来表示同一个 `row_dimension` 下多个 source 的顺序
  - 程序读取 Excel 模板时，会先按 `source_order` 排序，再按这个顺序拼接 source 结果
  - 如果一个维度只有一个 source，这个值通常就是 `1`
  - 如果一个维度有多个 source，例如 `Line` 再 `Site`，那就可以写成：
    - `Line` 的 `source_order = 1`
    - `Site` 的 `source_order = 2`
  - 这个字段不会出现在 JSON 里，因为 JSON 里的 `sources` 本身就是有序数组，顺序已经天然表达了 source 的先后关系
- `source_column`
- `split_position`
- `skip_empty_parts`
- `delimiter_1`
- `delimiter_2`
- ...

说明：

- 同一个 `name` 可以出现多行，表示同一个维度有多个 source
- `source_order` 控制 source 的拼接顺序
- `delimiter_1 / delimiter_2 / ...` 表示一个 source 可以有多个 delimiter

为什么 JSON 里没有 `source_order`：

- 因为 JSON 的 `sources` 是数组，天然就有顺序
- 例如：

```json
"sources": [
  { "column": "Line" },
  { "column": "Site" }
]
```

这里就已经表示先取 `Line`，再取 `Site`，不需要再额外写一个 `source_order`

为什么 Excel 里需要 `source_order`：

- 因为 Excel 是按“多行表示一个维度的多个 source”
- 如果不单独写 `source_order`，只靠行位置就不够稳定
- 加上这个字段后，你可以排序、插行、筛选之后仍然保持 source 的明确顺序

### 5.3 `analysis_groups`

一行表示一个 raw column。表头：

- `id`
- `display_name`
- `analysis_mode`
- `presentation_group`
- `unit`
- `column_order`
- `column_name`

### 5.4 `node_orders`

一行表示一条 node sequence。表头：

- `sequence_name`
- `node_1`
- `node_2`
- `node_3`
- ...

### 5.5 `golden_values`

表头：

- `key`
- `value`

### 5.6 `zscore_thresholds`

表头：

- `metric_key`
- `value`

其中：

- `metric_key = default` 表示默认 threshold

### 5.7 `golden_deviation_thresholds`

表头同上：

- `metric_key`
- `value`

### 5.8 `outlier_ratio_stats`

一行表示一个 ratio filter 项。表头：

- `id`
- `display_name`
- `group_by_dimension`
- `numerator`
- `filter_type`
- `filter_order`
- `filter_value`

其中：

- `filter_type` 允许值：
  - `chain`
  - `raw_column`
  - `logical_metric`

- 如果一个统计项没有任何 filter，也可以只留一行基础配置，把 `filter_type / filter_value` 留空

例子：

```text
new_ratio_by_node_all | New Outlier Ratio By Node | reliability_node | new_outlier_samples |            | 1 | 
total_ratio_by_node_link4 | Total Outlier Ratio By Node (Link4) | reliability_node | outlier_samples | chain | 1 | Link4
total_ratio_by_node_v_link1_1p8v | Total Outlier Ratio By Node (V_Link1_1p8V) | reliability_node | outlier_samples | raw_column | 1 | V_Link1_1p8V
```

## 6. 布尔值和常见输入格式

Excel / JSON 中布尔字段支持这些写法：

- 真值：
  - `1`
  - `true`
  - `yes`
  - `y`
- 假值：
  - `0`
  - `false`
  - `no`
  - `n`

如果布尔内容不是这些，会报错。

## 7. 主要校验规则

程序会自动校验这些内容：

- `row_dimension.name` 不能重复
- 每个 `row_dimension` 必须至少有一个 source
- 每个 source 必须有 `column`
- 如果 source 配了 `split_position`，必须同时有 `split_delimiters`
- `analysis_group.id` 不能重复
- `analysis_group.analysis_mode` 只能是：
  - `pooled_columns`
  - `per_column`
- 同一个 raw column 不能出现在多个 `analysis_groups`
- `report.outlier_fail_method` 只能是：
  - `modified_z_score`
  - `golden_deviation`
  - `zscore_and_golden`
  - `zscore_or_golden`
- `report.outlier_chain_fail_rule` 只能是：
  - `any_fail`
  - `all_fail`
- `report.outlier_ratio_stats[*].numerator` 只能是：
  - `new_outlier_samples`
  - `outlier_samples`
- `report.outlier_ratio_stats[*].group_by_dimension` 必须是已存在的 `row_dimensions.name`
- `node_orders` 中每条 sequence 不能为空
- 每条 node sequence 内部不能有重复 node
- 多条 node sequence 之间不能出现公共节点的反向顺序冲突

## 8. 常见问题

### 8.1 一个维度能不能从多个原始列来？

可以。给同一个 `row_dimension` 配多个 `sources` 即可。

### 8.2 一个 source 能不能用多个 delimiter？

可以。`split_delimiters` 是列表，例如：

```json
"split_delimiters": ["_", "｜"]
```

### 8.3 能不能一个维度里有的 source split，有的 source 不 split？

可以。

- 有 `split_position` 的 source 会先 split
- 没有 `split_position` 的 source 会直接取整格内容

### 8.4 `golden_values` 和 threshold override 的 key 应该写什么？

优先推荐：

- pooled 组：写 `group_id`
- per-column 组：写 `group_id::raw_column`

例如：

```json
"golden_values": {
  "link1_resistance": 99,
  "link1_current::I_Link1_1p8V": 9.6
}
```

### 8.5 为什么有的 template 字段在 Excel 里和 JSON 结构不完全一样？

因为 Excel 模板更偏向“方便人工编辑和校验”，所以做了表格化展开：

- `row_dimensions` 按 source 拆行
- `analysis_groups` 按 raw column 拆行
- `node_orders` 按 node 拆列

程序会把这些 sheet 再翻译回内部 JSON 结构。

## 9. 推荐做法

- `row_dimensions`
  - 尽量把一个维度的提取规则写清楚，不要混用太多 source，除非业务上真的需要重组

- `analysis_groups`
  - `id` 取稳定、短一点的业务名
  - `columns` 顺序尽量和实际展示顺序一致

- `golden_values`
  - 优先按 `group_id` 或 `group_id::raw_column` 写，不要过度依赖 `chain_name`

- `node_orders`
  - 如果业务里确实有多种 node 路径，优先写 `node_orders`
  - 公共节点顺序必须保持一致

- `outlier_ratio_stats`
  - 如果只是想看每个 node 新增失效比例，先从 `group_by_dimension=reliability_node + numerator=new_outlier_samples` 开始
  - 如果想只看某条链路或某个测试项，再加 `chains` 或 `raw_columns`

## 10. 相关命令

校验 template：

```bash
excel-data-analysis validate-template --input examples/chip_reliability_template.json
excel-data-analysis validate-template --input examples/chip_reliability_template.xlsx
```

JSON 转 Excel：

```bash
excel-data-analysis template-to-xlsx \
  --input examples/chip_reliability_template.json \
  --output examples/chip_reliability_template.xlsx
```

Excel 转 JSON：

```bash
excel-data-analysis template-to-json \
  --input examples/chip_reliability_template.xlsx \
  --output /tmp/chip_reliability_template.json
```
