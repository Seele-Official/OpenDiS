# PyDiS 接口文档

这份文档面向当前仓库打包出来的本地 `pydis` 包。

目标是说明打包后哪些接口可以稳定导入、这些接口各自负责什么、以及一套最小可运行的调用关系。这里优先记录当前 `pydis/__init__.py` 暴露出来的顶层 API，而不是所有内部实现细节。

## 导入方式

打包后的推荐导入方式：

```python
from pydis import (
    DisNode,
    DisEdge,
    Cell,
    DisNet,
    CalForce,
    MobilityLaw,
    TimeIntegration,
    Topology,
    Collision,
    Remesh,
    VisualizeNetwork,
    SimulateNetwork,
    CellList,
)

from pydis.framework.disnet_manager import DisNetManager
```

说明：

- `pydis` 顶层包导出的是建模、求力、迁移率、时间积分、拓扑操作、碰撞、重网格、可视化和模拟驱动相关的常用类。
- `DisNetManager` 没有放在顶层 `pydis` 中，当前仍需从 `pydis.framework.disnet_manager` 导入。
- 打包结果通常还会附带 `pydis_lib`。它是本地编译出的加速扩展，`CalForce` 和 `Collision` 在可用时会优先使用它；不可用时会自动退回纯 Python 实现。

## 顶层公开接口

### 数据结构

#### `DisNode`

节点属性对象，核心字段：

- `R`: 节点坐标，`numpy.ndarray(shape=(3,))`
- `constraint`: 节点约束类型

常用枚举：

- `DisNode.Constraints.UNCONSTRAINED`
- `DisNode.Constraints.PINNED_NODE`
- `DisNode.Flags.*`

常用方法：

- `copy()`
- `view()`

#### `DisEdge`

位错段属性对象，核心字段：

- `source_tag`
- `target_tag`
- `burg_vec`
- `plane_normal`，如果构造时提供

常用方法：

- `burg_vec_from(from_tag)`
- `copy()`
- `view()`

#### `Cell`

模拟胞元和边界条件描述，核心字段：

- `h`: 3x3 胞元矩阵
- `origin`
- `is_periodic`: 三个方向是否周期

常用方法：

- `map(dr)`: 将位移映射回胞元
- `closest_image(Rref, R)`: 找最近镜像
- `center()`
- `volume()`

#### `DisNet`

PyDiS 的核心网络对象，保存节点、位错段和胞元，并提供拓扑操作。

常见构造方式：

```python
G = DisNet(cell=cell, rn=rn, links=links)
```

其中：

- `rn` 是节点数组，至少包含坐标；若带第 4 列则可包含节点约束
- `links` 是段数组，通常包含端点索引、Burgers 矢量和滑移面法向

常用查询接口：

- `nodes(tag)`
- `neighbors_tags(tag)`
- `neighbors_dict(tag)`
- `neighbor_segments_dict(tag)`
- `all_nodes_tags()`
- `all_segments_tags()`
- `num_nodes()`
- `num_segments()`

常用几何/数据接口：

- `pos_array()`
- `get_segs_data_with_positions()`
- `export_data()`
- `import_data(data)`

常用拓扑接口：

- `insert_node_between(tag1, tag2, new_tag, position)`
- `remove_two_arm_node(tag)`
- `split_node(tag, pos1, pos2, nbrs_to_split)`
- `merge_node(tag1, tag2)`
- `is_sane()`

### 管理器

#### `DisNetManager`

`DisNetManager` 用来包装 `DisNet`，并作为各个算法模块的统一输入。

推荐初始化方式：

```python
DM = DisNetManager(G)
```

常用接口：

- `get_disnet(disnet_type=None)`
- `write_json(path)`
- `read_json(path)`
- `is_sane()`
- `cell`
- `num_nodes()`
- `num_segments()`

当前 `SimulateNetwork`、`CalForce`、`MobilityLaw`、`Topology`、`Collision`、`Remesh`、`VisualizeNetwork` 的方法签名都以 `DisNetManager` 为主，而不是直接传 `DisNet`。

### 物理与算法模块

#### `CalForce`

负责根据网络和外加应力计算节点力。

构造参数：

- `state`: 读取 `mu`、`nu`、`a` 等材料参数
- `Ec`: 线张力相关能量参数
- `force_mode`: 当前代码里稳定可见的是：
  - `'LineTension'`
  - `'Elasticity_SBA'`
  - `'Elasticity_SBN1_SBA'`

主接口：

- `NodeForce(DM, state) -> dict`
- `OneNodeForce(DM, state, tag, update_state=True)`

写回的常用状态字段：

- `state["nodeforce_dict"]`
- `state["segforce_dict"]`
- 兼容数组形式的 `state["nodeforces"]` 和 `state["nodeforcetags"]`

说明：

- 如果 `pydis_lib` 可用，部分解析力学计算会优先走扩展实现。
- `OneNodeForce` 的部分高阶模式仍未完整实现，当前最稳的是示例里在用的 `LineTension`。

#### `MobilityLaw`

负责把节点力转换为节点速度。

构造参数：

- `state`: 可读取 `mob`
- `mobility_law`:
  - `'Relax'`
  - `'SimpleGlide'`
- `vmax`

主接口：

- `Mobility(DM, state) -> dict`
- `OneNodeMobility(DM, state, tag, f, update_state=True)`

写回的常用状态字段：

- `state["vel_dict"]`
- 兼容数组形式的 `state["nodevels"]` 和 `state["nodeveltags"]`

#### `TimeIntegration`

负责根据速度推进网络位置。

构造参数：

- `integrator`: 当前稳定实现为 `'EulerForward'`
- `dt`

主接口：

- `Update(DM, state) -> dict`

写回的常用状态字段：

- `state["dt"]`
- `state["time"]`

#### `Topology`

处理多臂节点分裂等拓扑事件。

构造参数：

- `split_mode`: 当前实现为 `'MaxDiss'`
- `force`: 通常传入 `CalForce` 实例
- `mobility`: 通常传入 `MobilityLaw` 实例

主接口：

- `Handle(DM, state) -> dict`

写回或依赖的状态字段：

- `state["nodeflag_dict"]`
- `state["nodeforce_dict"]`
- `state["vel_dict"]`

说明：

- `Topology` 对 `force` 和 `mobility` 的模块来源有检查，默认应使用同一套 `pydis` 组件组合。

#### `Collision`

处理段间碰撞。

构造参数：

- `collision_mode`: 当前实现为 `'Proximity'`
- `nbrlist`: 需要传入 `CellList`
- `state`: 读取 `rann`

主接口：

- `HandleCol(DM, state) -> dict`

说明：

- 若 `pydis_lib` 可用，最近距离计算优先走扩展版本。
- 该模块依赖 `Topology` 预先建立的 `state["nodeflag_dict"]`。

#### `Remesh`

根据长度规则粗化或细化网络。

构造参数：

- `remesh_rule`: 当前实现为 `'LengthBased'`
- `state`: 读取 `maxseg` 和 `minseg`

主接口：

- `Remesh(DM, state) -> dict`

#### `CellList`

用于邻近搜索的胞元链表，目前主要给 `Collision` 使用。

构造参数：

- `cell`
- `n_div`

主接口：

- `sort_points_to_list(R)`
- `iterate_nbr_pairs(use_cell_list=True)`

注意：

- 文档和实现都表明它在三方向周期边界下最合适。

#### `VisualizeNetwork`

绘制当前位错网络。

主接口：

- `plot_disnet(DM, state={}, plot_links=True, trim=False, fig=None, ax=None, block=False, pause_seconds=0.01)`

依赖：

- `matplotlib`
- `mpl_toolkits.mplot3d`

#### `SimulateNetwork`

模拟主调度器，负责把求力、迁移率、时间积分、拓扑、碰撞、重网格、输出和可视化串起来。

构造参数里最重要的是：

- `calforce`
- `mobility`
- `timeint`
- `topology`
- `collision`
- `remesh`
- `vis`
- `dt0`
- `max_step`
- `loading_mode`
- `applied_stress`
- `print_freq`
- `plot_freq`
- `write_freq`
- `write_dir`
- `save_state`

主接口：

- `step(DM, state) -> dict`
- `run(DM, state) -> dict`

说明：

- 当前实现里 `loading_mode` 实际只接受 `'stress'`。
- 文件输出通过 `DisNetManager.write_json()` 完成。

## 最小调用链

最常见的一套 PyDiS 纯 Python 工作流是：

```python
import numpy as np

from pydis import (
    Cell,
    DisNet,
    CalForce,
    MobilityLaw,
    TimeIntegration,
    Topology,
    SimulateNetwork,
)
from pydis.framework.disnet_manager import DisNetManager

cell = Cell(h=10.0 * np.eye(3), is_periodic=[True, True, True])

rn = np.array([
    [4.0, 5.0, 5.0],
    [6.0, 5.0, 5.0],
])

links = np.array([
    [0, 1, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
])

state = {
    "mu": 160e9,
    "nu": 0.31,
    "a": 0.01,
    "maxseg": 0.3,
    "minseg": 0.1,
    "rann": 0.02,
}

DM = DisNetManager(DisNet(cell=cell, rn=rn, links=links))

calforce = CalForce(state=state, force_mode="LineTension")
mobility = MobilityLaw(state=state, mobility_law="Relax")
timeint = TimeIntegration(state=state, integrator="EulerForward", dt=1.0e-8)
topology = Topology(state=state, split_mode="MaxDiss", force=calforce, mobility=mobility)

sim = SimulateNetwork(
    state=state,
    calforce=calforce,
    mobility=mobility,
    timeint=timeint,
    topology=topology,
    collision=None,
    remesh=None,
    max_step=10,
    loading_mode="stress",
    applied_stress=np.zeros(6),
)

sim.run(DM, state)
```

如果需要碰撞处理，再额外补：

```python
from pydis import CellList, Collision

nbrlist = CellList(cell=DM.cell, n_div=[4, 4, 4])
collision = Collision(state=state, collision_mode="Proximity", nbrlist=nbrlist)
```

## 状态字典约定

当前 `pydis` 各模块通过同一个 `state: dict` 交换数据。常见字段如下：

- 输入参数：
  - `mu`
  - `nu`
  - `a`
  - `mob`
  - `maxseg`
  - `minseg`
  - `rann`
  - `applied_stress`
- 运行期输出：
  - `nodeforce_dict`
  - `segforce_dict`
  - `vel_dict`
  - `nodeflag_dict`
  - `dt`
  - `time`
  - `istep`

这套字段约定目前是代码事实上的接口，不是显式 schema。写自定义模块时，最好与现有字段名保持一致。

## 稳定性边界

建议视为相对稳定、适合打包后直接使用的接口：

- `pydis.__init__` 暴露出的顶层类
- `pydis.framework.disnet_manager.DisNetManager`
- 示例脚本已经在使用的构造参数和调用方式

不建议在外部代码里强依赖的部分：

- `pydis.*` 子模块里的内部辅助函数
- `framework` 下的 base class 细节
- `graph` 目录里的底层图实现
- 尚未实现完成、但名字已经出现的高阶模式

## 参考入口

如果需要看真实用法，优先参考：

- [examples/01_loop/test_disl_loop_pydis.py](/home/seele/OpenDiS/examples/01_loop/test_disl_loop_pydis.py)
- [examples/03_binary_junction/test_binary_junction_pydis.py](/home/seele/OpenDiS/examples/03_binary_junction/test_binary_junction_pydis.py)
- [tutorials/01_initial_configurations/initial_configurations.py](/home/seele/OpenDiS/tutorials/01_initial_configurations/initial_configurations.py)
