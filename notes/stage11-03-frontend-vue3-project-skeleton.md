# 阶段 11 第 3 节：前端技术选型与项目骨架

## 本节定位

本节开始正式创建阶段 11 的真实前端项目。

前端固定技术栈：

```text
Vue3 + TypeScript + Vite + Element Plus
Vue Router + Pinia + Axios
```

本节不是做完整业务功能，而是先把前端工作台骨架搭起来，让后续订单、工单、AI 对话、知识库、评估和配置页面都有承载位置。

## 本节完成内容

新增前端项目：

```text
projects/customer-service-console
```

已完成：

- 创建 Vue3 + TypeScript + Vite 项目。
- 安装 Element Plus、Element Plus Icons、Vue Router、Pinia、Axios。
- 接入 Element Plus。
- 接入 Vue Router。
- 接入 Pinia。
- 新增 Axios client 基础。
- 新增 `.env.example`。
- 替换默认 Vite 示例页。
- 创建后台工作台布局。
- 创建阶段 11 需要的第一批页面骨架。

## 页面骨架

当前已有页面：

- 运营概览。
- AI 客服。
- 我的订单。
- 我的工单。
- 工单工作台。
- 知识库管理。
- AI 评估。
- 系统配置。

这些页面现在主要是静态骨架，后续会逐步接入真实 Java 和 Python API。

## 当前前端边界

当前已经做的是：

```text
真实前端项目
真实路由
真实组件库
真实状态管理
真实 API client 基础
静态业务数据展示
```

当前还没做的是：

```text
登录接口
真实 Java API
真实 Python AI API
真实订单数据
真实工单数据
真实 RAG 问答
真实模型调用
```

这符合阶段 11 的实施顺序：先让前端有完整壳子，再逐步接真实业务和 AI 链路。

## 为什么选择 Vue3 + Element Plus

这个项目本质是客服工作台 / 后台管理系统，不是营销网站。

Vue3 + Element Plus 适合这个场景，因为：

- 你更熟悉 Vue3 体系。
- Element Plus 提供成熟的表格、表单、菜单、弹窗、分页、Tabs、Drawer。
- TypeScript 适合约束用户、订单、工单、AI 消息等接口类型。
- Vue Router 适合多页面工作台。
- Pinia 适合保存当前用户、角色、权限和全局状态。
- Axios 适合统一封装 Java API 和 Python AI API。

## 本节验证

已运行：

```powershell
npm run build
```

结果：

```text
构建通过。
```

构建时出现 chunk size warning，原因是当前全量引入 Element Plus 后打包体积较大。

当前阶段先接受这个提醒，因为第 3 节重点是搭骨架。后续如果需要优化，可以做：

- Element Plus 按需加载。
- 路由懒加载。
- 分包。

## 手动运行

在 PowerShell 中执行：

```powershell
cd D:\wendang\java+python+ai\projects\customer-service-console
npm run dev
```

浏览器打开 Vite 输出的地址，一般是：

```text
http://localhost:5173
```

## 本节练习

### 练习 1：为什么前端不应该保存模型 API Key？

参考答案：

浏览器前端代码会发送到用户机器上，任何写在前端里的 API Key 都可能被看到。模型 API Key 应该放在后端环境变量里，由 Python AI 服务读取。

### 练习 2：Vue Router 在这个项目里负责什么？

参考答案：

Vue Router 负责页面路由，比如运营概览、AI 客服、订单、工单、知识库、评估和配置页面之间的切换。

### 练习 3：Pinia 在这个项目里先负责什么？

参考答案：

当前先用 Pinia 保存当前用户、角色和租户信息。后续登录真实化后，会扩展为登录状态、权限菜单和 token 辅助状态。

## 自测题

### 自测 1：当前前端项目目录是什么？

答案：

```text
projects/customer-service-console
```

### 自测 2：当前页面为什么还用静态数据？

答案：

因为本节目标是先搭前端骨架，不提前和 Java/Python API 纠缠。后续会按阶段顺序逐步接真实接口。

### 自测 3：下一节应该做什么？

答案：

下一节建议进入登录与用户角色最小闭环，开始让前端从“静态工作台骨架”进入“带身份边界的真实业务入口”。
