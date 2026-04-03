# `reference_dims` 和 `filter` 使用说明

这两个参数都用于 `build-golden` 流程，但职责完全不同：

- `filter`：决定“哪些数据允许参与建 golden”
- `reference_dims`：决定“参与的数据要按哪些维度分别建几套 golden”

可以把它们简单理解成：

- `filter` = `WHERE`
- `reference_dims` = `GROUP BY`

另外，系统无论如何都会再按 `logical_metric` 分开，所以不同测试项目不会被混到同一个 golden 里。

---

## 1. `filter` 是什么

`filter` 用来筛选参与建 golden 的原始记录。

当前版本只支持最简单的精确匹配：

```text
key=value
```

例如：

```text
reliability_node=T0
sample_id=S001
site_id=A
temp=27
```

多个 `filter` 同时存在时，关系是 `AND`，也就是必须同时满足：

```bash
--filter reliability_node=T0 --filter site_id=A
```

含义：

- 只使用 `reliability_node == T0`
- 且 `site_id == A`

的记录参与建 golden。

### 当前支持

- 精确匹配 `key=value`
- 多个条件同时使用

### 当前不支持

- `>`
- `<`
- `>=`
- `<=`
- `!=`
- `IN`
- 模糊匹配
- 正则
- `OR`

所以目前 `filter` 的能力就是“按维度值精确筛选”。

---

## 2. `reference_dims` 是什么

`reference_dims` 是一个维度名列表，用来决定 golden 要按哪些业务维度拆分。

这些维度名必须来自模板里的 `row_dimensions.name`。

以当前项目里的真实样例模板为例，可用维度通常包括：

- `sample_id`
- `reliability_node`
- `repeat_id`
- `site_id`
- `temp`

它们来自模板对输入表行信息的拆解，比如当前样例里：

- `sample_id / reliability_node / repeat_id` 是从 `recordName` 拆出来的
- `site_id` 来自 `Site`
- `temp` 来自 `temp`

### 常见写法

#### `reference_dims = sample_id`

含义：

- 每颗样品各自有一套 golden

结果：

- `S001` 的 golden 和 `S002` 的 golden 可能不同

适合：

- 看单颗样品相对自己基准是否漂移

#### `reference_dims = reliability_node`

含义：

- 每个 node 单独建一套 golden

结果：

- `T0` 一套
- `T1` 一套
- `T2` 一套

适合：

- 节点之间天然分布不同的情况

#### `reference_dims = sample_id,reliability_node`

含义：

- 每颗样品每个 node 都单独建 golden

适合：

- 需要非常细粒度对比

注意：

- 分组太细时，每组样本数量会变少，golden 稳定性也会下降

#### `reference_dims = site_id`

含义：

- 每个 site 各自一套 golden

适合：

- A/B site 本身分布不同，不适合混合统计

#### `reference_dims = temp`

含义：

- 每个温度单独建 golden

适合：

- 不同温度下数据分布本来就不同

#### `reference_dims = sample_id,site_id`

含义：

- 每颗样品每个 site 各自一套 golden

#### `reference_dims = []`

含义：

- 不按任何业务维度拆分
- 所有满足 `filter` 的记录，共用一套 golden

注意：

- 虽然没有业务维度分组，但系统仍然会按 `logical_metric` 分开
- 也就是说“所有样品共用同一个测项的 golden”，而不是所有测项混成一团

适合：

- 想让所有样品对照同一套公共基准

---

## 3. 两者如何组合

建 golden 的逻辑顺序是：

1. 先按 `filter` 筛掉不符合条件的数据
2. 再按 `reference_dims` 分组
3. 每组内再按 `logical_metric` 分开统计

所以：

- `filter` 控制参与范围
- `reference_dims` 控制分组粒度

---

## 4. 常见组合示例

### 示例 1：每颗样品用自己的 T0 做基准

```bash
--reference-dims sample_id
--filter reliability_node=T0
```

含义：

- 只用 T0 的数据
- 每颗样品分别建自己的 golden

适合：

- “每颗 sample 后续相对自己 T0 是否漂移”

---

### 示例 2：所有样品共用 T0 基准

```bash
--reference-dims ""
--filter reliability_node=T0
```

含义：

- 只用 T0 数据
- 不按样品拆分
- 所有样品共用同一套 T0 golden

适合：

- “大家都和统一群体基准比”

---

### 示例 3：每颗样品每个 site 用自己的 T0 做基准

```bash
--reference-dims sample_id,site_id
--filter reliability_node=T0
```

含义：

- 只用 T0 数据
- 每颗样品的每个 site 各自一套 golden

适合：

- site 差异比较大，不想混算

---

### 示例 4：只使用 27 度、A site 的 T0 建 golden

```bash
--reference-dims sample_id
--filter reliability_node=T0
--filter temp=27
--filter site_id=A
```

含义：

- 只在指定条件下取 baseline

适合：

- 测试条件很多，但只想选某个固定条件做 golden

---

### 示例 5：按温度分别建公共 golden

```bash
--reference-dims temp
--filter reliability_node=T0
```

含义：

- 只用 T0
- 不同温度分别建一套公共 golden

适合：

- 温度是主要影响因素

---

## 5. 为什么 `golden.json` 里不同样品会有不同 golden

如果你在建 golden 时使用了：

```bash
--reference-dims sample_id
--filter reliability_node=T0
```

那系统会：

- 只用 `T0` 的数据
- 再按 `sample_id` 分组

于是：

- `S001` 用自己的 T0 数据算一套 golden
- `S002` 用自己的 T0 数据算另一套 golden

所以不同样品的 golden 本来就会不同。

这不是异常，而是 `reference_dims=sample_id` 的预期行为。

如果你想让所有样品共用一套 golden，就不要把 `sample_id` 放进 `reference_dims`。

---

## 6. 怎么选才合理

### 想看“每颗样品是否相对自己漂移”

推荐：

```text
filter = reliability_node=T0
reference_dims = sample_id
```

### 想看“所有样品是否相对统一基准异常”

推荐：

```text
filter = reliability_node=T0
reference_dims = []
```

### 想消除 site 差异

推荐：

- 把 `site_id` 放进 `reference_dims`

### 想限制只在某个测试条件下建 golden

推荐：

- 把这些条件放进 `filter`

例如：

- `temp=27`
- `site_id=A`

---

## 7. 最容易踩的坑

### `reference_dims` 太多

问题：

- 分组太细
- 每组数据太少
- golden 不稳定

### `reference_dims` 太少

问题：

- 本来不同分布的数据被混在一起
- golden 会失真

### `filter` 写了不存在的维度名

问题：

- 可能直接筛不出数据

### `filter` 的值和模板拆解后的值不一致

例如模板里是：

- `T0`

但你写成：

- `t0`

这样就匹配不到。

---

## 8. 建议记忆方式

一句话版本：

- `filter`：先选哪些数据能进来
- `reference_dims`：再决定这些数据分几桶来建 golden

更短一点：

- `filter` 看范围
- `reference_dims` 看分组

---

## 9. 当前项目里的推荐起步方案

对于芯片可靠性场景，最推荐先从这两种开始：

### 方案 A：每颗样品用自己的 T0 作为基准

```bash
--reference-dims sample_id
--filter reliability_node=T0
```

### 方案 B：所有样品共用一套 T0 基准

```bash
--reference-dims ""
--filter reliability_node=T0
```

这两种先跑通后，再决定是否需要把：

- `site_id`
- `temp`
- 其他业务维度

也纳入 `reference_dims` 或 `filter`。
