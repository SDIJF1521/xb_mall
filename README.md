<div align="center">

# 🛒 XB Mall 电商平台

![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?logo=vue.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-005571?logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-ES2022-3178C6?logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)

一个现代化的全栈电商平台系统，采用前后端分离架构设计。

</div>

---

## 📁 项目结构

```text
xb_mall/
├── porject/              # 🖥️  前端项目 (Vue.js + Vite)
│   ├── src/              # 源代码
│   ├── public/           # 静态资源
│   ├── node_modules/     # 依赖包
│   ├── package.json      # 项目配置
│   └── ...
├── serve/                # 🔧  后端项目 (FastAPI)
│   ├── main.py           # 主应用入口
│   ├── routes/           # API 路由
│   ├── services/         # 业务逻辑服务
│   ├── data/             # 数据访问层
│   ├── config/           # 配置文件
│   ├── logs/             # 📝 日志目录
│   └── ...
└── README.md             # 📄 项目文档
```

## ⚙️ 技术栈

<div align="center">

| 技术类别              | 技术选型                                                       | 版本/标准 |
| --------------------- | -------------------------------------------------------------- | --------- |
| **前端框架**    | [Vue.js](https://vuejs.org/)                                      | 3.x       |
| **构建工具**    | [Vite](https://vitejs.dev/)                                       | 最新版    |
| **UI 框架**     | [Element Plus](https://element-plus.org/)                         | 最新版    |
| **状态管理**    | [Pinia](https://pinia.vuejs.org/)                                 | 最新版    |
| **图表库**      | [ECharts](https://echarts.apache.org/)                            | 最新版    |
| **HTTP 客户端** | [Axios](https://axios-http.com/)                                  | 最新版    |
| **后端框架**    | [FastAPI](https://fastapi.tiangolo.com/)                          | 0.104+    |
| **编程语言**    | [Python](https://www.python.org/)                                 | 3.10+     |
| **数据库**      | [MySQL](https://www.mysql.com/), [MongoDB](https://www.mongodb.com/) | 最新版    |
| **缓存**        | [Redis](https://redis.io/)                                        | 最新版    |
| **任务调度**    | [APScheduler](https://apscheduler.readthedocs.io/)                | 最新版    |

</div>

<br>

### 🖥️ 前端技术

- **框架**: Vue.js 3 - 渐进式 JavaScript 框架
- **构建工具**: Vite - 下一代前端构建工具
- **UI 框架**: Element Plus - 企业级组件库
- **状态管理**: Pinia - 轻量级状态管理库
- **图表库**: ECharts - 强大的可视化图表库
- **HTTP 客户端**: Axios - Promise 基于的 HTTP 客户端

### 🔧 后端技术

- **框架**: FastAPI - 现代高性能 Web 框架
- **数据库**: MySQL（关系型）, MongoDB（文档型）
- **缓存**: Redis - 内存数据结构存储
- **任务调度**: APScheduler - Python 任务调度库
- **认证**: JWT Token - 无状态身份验证
- **CORS**: 支持跨域资源共享

## ✨ 核心功能

<div align="center">

| 功能模块           | 功能描述                       | 技术实现           |
| ------------------ | ------------------------------ | ------------------ |
| **用户管理** | 用户注册、登录、密码重置       | JWT Token 认证     |
| **商家管理** | 商家入驻申请、审核、状态管理   | 审核流程自动化     |
| **商品管理** | 商品上架、下架、编辑、库存管理 | 多数据库支持       |
| **店铺管理** | 店铺创建、编辑、个性化设置     | 自定义店铺配置     |
| **权限管理** | 用户角色分配、权限控制         | RBAC 权限模型      |
| **数据统计** | 用户增长、销售数据、商家统计   | ECharts 图表展示   |
| **实时监控** | 用户在线状态、系统健康度       | WebSocket 实时通信 |

</div>

<br>

### 🖥️ 前端功能亮点

- 📝 **用户注册/登录** - 安全的身份验证机制
- 🔐 **验证码系统** - 防止机器人攻击
- 🔄 **密码重置** - 安全的密码找回流程
- 👥 **商家管理** - 商家信息管理与审核
- 📦 **商品管理** - 商品信息全生命周期管理
- 🏪 **店铺管理** - 店铺个性化配置与管理
- 🔐 **用户权限管理** - 细粒度权限控制
- 👑 **角色分配** - 灵活的角色管理系统

### 🔧 后端功能亮点

- 🔐 **用户认证与授权** - JWT Token 身份验证
- ✅ **商家申请审核** - 自动化审核流程
- 📦 **商品上下架管理** - 商品生命周期管理
- 📊 **库存管理** - 实时库存跟踪
- 🏷️ **分类管理** - 商品分类体系管理
- 👥 **用户在线状态管理** - 实时用户状态监控
- 💾 **数据缓存服务** - 高性能缓存策略

## 项目维护

- **许可证**: GPLv3
- **作者**: SDIJF1521
- **版本**: 0.2.0

## 🤝贡献指南

欢迎提交 Issue 和 Pull Request 来改进此项目。

## 🙏致谢

感谢所有为本项目做出贡献的人。
