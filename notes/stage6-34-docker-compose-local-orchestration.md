# 阶段 6 第 34 节：Docker Compose 本地编排

本节主题：

Docker Compose 本地编排。

前面几节我们一直在做生产化策略：

```text
timeout
retry
rate limit
circuit breaker
degradation
```

这些都是“服务已经运行起来以后”的稳定性策略。

这一节开始补另一个生产化基础：

服务怎么一起运行。

现在项目里已经不只是一个 Python 文件。

它至少包含：

```text
ai-service
java-mock-service
Qdrant
Milvus
```

以后还可能有：

```text
前端工作台
真实 Java Spring Boot 服务
PostgreSQL
Redis
OpenTelemetry Collector
Prometheus
Grafana
```

如果每个服务都手动开一个终端启动，会越来越乱。

Docker Compose 解决的就是这个问题：

用一个 YAML 文件描述一组服务，让它们按同一套规则启动、停止、联网、挂载数据、读取配置。

---

## 一、本节学习目标

学完本节，你要能讲明白：

1. Docker 是什么。
2. Docker Compose 是什么。
3. Docker 和 Docker Compose 的区别。
4. 为什么多服务项目需要 Compose。
5. `compose.yml` 是什么。
6. `services` 是什么。
7. `image` 是什么。
8. `command` 是什么。
9. `ports` 是什么。
10. `environment` 是什么。
11. `env_file` 是什么。
12. Compose 根目录 `.env` 和服务里的 `env_file` 有什么区别。
13. `volumes` 是什么。
14. bind mount 和 named volume 有什么区别。
15. `networks` 是什么。
16. 为什么容器之间用服务名访问。
17. `depends_on` 能做什么，不能做什么。
18. `healthcheck` 是什么。
19. `profiles` 是什么。
20. 为什么 Qdrant 和 Milvus 适合放到 profile 里。
21. Windows 项目目录和 VMware Ubuntu Docker 的关系。
22. 为什么 Docker 在 Ubuntu 时，不能直接假设能挂载 Windows 的 `D:\...` 路径。
23. 为什么不能把真实 API Key 写进 compose 文件。
24. 为什么本节不直接改成“全服务生产部署”。

---

## 二、官方资料

本节参考以下官方资料：

1. Docker Compose overview
   https://docs.docker.com/compose/

   重点：Docker Compose 用来定义和运行多容器应用，可以用一个 YAML 文件控制服务、网络、卷，并用一个命令启动整个应用栈。

2. Docker Compose file reference
   https://docs.docker.com/reference/compose-file/

   重点：Compose Specification 是推荐的 Compose 文件格式，用来定义 services、networks、volumes 等。

3. Docker Compose services reference
   https://docs.docker.com/reference/compose-file/services/

   重点：service 描述容器运行所需的约束和配置，比如 image、ports、environment、volumes、depends_on。

4. Docker Compose environment variables
   https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/

   重点：`env_file` 可以给容器设置环境变量，也能避免把大量环境变量直接写在 compose 文件里。

5. Docker Compose variable interpolation
   https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/

   重点：Compose 会从 shell、`--env-file`、项目根目录 `.env` 读取变量来替换 compose 文件里的 `${VAR}`。

6. Docker Compose startup order
   https://docs.docker.com/compose/how-tos/startup-order/

   重点：`depends_on` 可以控制启动和停止顺序；默认只等容器 running，不等服务 ready。要等健康状态，需要配合 `healthcheck` 和 `condition: service_healthy`。

7. Docker Compose profiles
   https://docs.docker.com/compose/how-tos/profiles/

   重点：profiles 可以让某些服务只在指定场景启动。没有 profiles 的核心服务默认启动，有 profiles 的服务要显式启用。

8. Qdrant installation
   https://qdrant.tech/documentation/installation/

   重点：Qdrant 可以通过 Docker 和 Docker Compose 运行，本地开发可以用 Docker Compose。

9. Milvus standalone with Docker Compose
   https://milvus.io/docs/install_standalone-docker-compose.md

   重点：Milvus 官方提供 standalone Docker Compose 方式，通常包含 Milvus、etcd、MinIO。

---

## 三、承接当前项目

当前项目结构大致是：

```text
D:/wendang/java+python+ai
  projects/
    ai-service/
    java-mock-service/
    python-basics/
  notes/
  docs/
  README.md
```

当前最重要的两个服务是：

```text
projects/ai-service
projects/java-mock-service
```

注意：

`java-mock-service` 现在还不是真正的 Java/Spring Boot 服务。

它目前是一个用 FastAPI 写的 mock 业务服务。

为什么叫这个名字？

因为它在架构角色上模拟 Java 业务后端。

真实目标是：

```text
Python AI Service
-> Java Business Service
-> 订单、工单、权限等业务系统
```

当前学习阶段先是：

```text
Python AI Service
-> Java Mock Service
-> 内存订单 / 内存工单
```

Compose 会把这两个服务放到一个网络里。

这样 `ai-service` 不再用：

```text
http://127.0.0.1:8001
```

访问 mock 服务。

而是在容器网络里用：

```text
http://java-mock-service:8001
```

这就是容器服务名访问。

---

## 四、基础知识铺垫

这一部分很重要。

Docker Compose 不是背命令。

你要理解它在解决什么工程问题。

### 4.1 Docker 是什么

Docker 是容器工具。

容器可以把程序和它的运行环境打包在一起。

比如：

Python 版本。

系统依赖。

启动命令。

环境变量。

网络端口。

文件挂载。

你可以把容器理解成：

一个隔离的运行环境。

它不是完整虚拟机。

它比虚拟机轻。

但它能让应用在更一致的环境里运行。

### 4.2 Docker Image 是什么

image 是镜像。

它像一个模板。

比如：

```text
qdrant/qdrant:v1.18.2
milvusdb/milvus:v3.0-beta
ghcr.io/astral-sh/uv:python3.12-bookworm-slim
```

这些都是镜像。

镜像本身不会运行。

它只是定义了运行环境。

用镜像创建出来并正在运行的实例，叫 container。

### 4.3 Container 是什么

container 是容器。

它是镜像运行起来后的实例。

一个镜像可以启动多个容器。

比如：

同一个 Python 镜像可以启动：

```text
ai-service 容器
java-mock-service 容器
```

它们用同一个基础镜像。

但挂载不同目录。

执行不同启动命令。

暴露不同端口。

### 4.4 Docker Compose 是什么

Docker Compose 是管理多个容器的工具。

Docker 官方文档说，Compose 是定义和运行多容器应用的工具。

你写一个 YAML 文件。

里面描述：

有哪些服务。

每个服务用什么镜像。

每个服务怎么启动。

每个服务暴露什么端口。

服务之间怎么联网。

哪些数据要持久化。

然后执行：

```bash
docker compose up
```

Compose 会帮你创建网络、卷、容器，并启动服务。

### 4.5 Docker 和 Docker Compose 的区别

Docker 更像是单容器操作工具。

比如：

```bash
docker run qdrant/qdrant
docker ps
docker logs qdrant
docker stop qdrant
```

Docker Compose 更像是多服务应用栈管理工具。

比如：

```bash
docker compose up -d
docker compose ps
docker compose logs -f ai-service
docker compose down
```

你可以这样理解：

Docker 管一个容器很方便。

Compose 管一组容器更方便。

### 4.6 为什么本项目需要 Compose

因为现在我们已经有多个服务。

如果手动启动，会变成：

终端 1：

```bash
cd projects/java-mock-service
uv run uvicorn app.main:app --port 8001
```

终端 2：

```bash
cd projects/ai-service
uv run uvicorn app.main:app --port 8000
```

终端 3：

```bash
docker run qdrant/qdrant
```

终端 4：

```bash
docker compose up milvus
```

这很容易乱。

Compose 把这些启动规则写到一个文件里。

以后你只看一个 `compose.yml`，就知道本地环境怎么跑。

### 4.7 compose.yml 是什么

`compose.yml` 是 Docker Compose 的配置文件。

它通常放在项目根目录。

本节新增：

```text
compose.yml
```

它定义了：

```text
java-mock-service
ai-service
qdrant
milvus-etcd
milvus-minio
milvus-standalone
```

其中：

`java-mock-service` 和 `ai-service` 是默认启动的核心服务。

`qdrant` 放在 `qdrant` profile 里。

`milvus-*` 放在 `milvus` profile 里。

### 4.8 services 是什么

`services` 是 Compose 文件的核心。

它表示：

这个应用栈里有哪些服务。

比如：

```yaml
services:
  ai-service:
    image: ...
  java-mock-service:
    image: ...
```

一个 service 通常对应一个容器。

但更准确地说，service 是“容器模板”。

Compose 会根据 service 配置创建容器。

### 4.9 image 是什么

`image` 指定服务使用哪个镜像。

例如：

```yaml
image: ghcr.io/astral-sh/uv:python3.12-bookworm-slim
```

意思是：

用一个已经带 Python 3.12 和 uv 的镜像启动容器。

本节没有写 Dockerfile。

原因是：

这一节目标是先学 Compose 编排。

我们用现成镜像运行已有项目，减少 Dockerfile 复杂度。

后续如果学习真正部署，再补 Dockerfile 和镜像构建。

### 4.10 command 是什么

`command` 是容器启动后执行的命令。

比如：

```yaml
command: >
  sh -lc "uv sync --frozen &&
  uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

它做两件事：

先同步依赖。

再启动 FastAPI 服务。

为什么用 `--host 0.0.0.0`？

因为容器里的服务如果只监听 `127.0.0.1`，外部访问不到。

容器服务要让宿主机访问，通常要监听 `0.0.0.0`。

### 4.11 ports 是什么

`ports` 是端口映射。

例如：

```yaml
ports:
  - "8000:8000"
```

左边是宿主机端口。

右边是容器端口。

意思是：

访问宿主机的 8000 端口，会转发到容器里的 8000 端口。

如果写：

```yaml
"6333:6333"
```

就是把宿主机 6333 映射到 Qdrant 容器 6333。

如果宿主机已经有容器占用了 6333，就会冲突。

你之前已经在 Ubuntu Docker 里启动过 Qdrant。

所以如果那个旧 Qdrant 还在运行，再启动本节 Compose 的 qdrant profile，可能会端口冲突。

### 4.12 environment 是什么

`environment` 是写入容器内部的环境变量。

例如：

```yaml
environment:
  JAVA_MOCK_SERVICE_BASE_URL: http://java-mock-service:8001
```

这个变量会被 `ai-service` 读取。

它告诉 `ai-service`：

在 Compose 网络里，Java mock 服务地址是：

```text
http://java-mock-service:8001
```

不是：

```text
http://127.0.0.1:8001
```

这点非常关键。

### 4.13 容器里的 127.0.0.1 是谁

容器里的 `127.0.0.1` 指的是容器自己。

不是宿主机。

不是另一个容器。

所以在 `ai-service` 容器里：

```text
http://127.0.0.1:8001
```

表示访问 `ai-service` 容器自己的 8001 端口。

但 Java mock 服务在另一个容器里。

所以要用服务名：

```text
http://java-mock-service:8001
```

Compose 会给同一个网络里的服务做 DNS 解析。

### 4.14 env_file 是什么

`env_file` 是把一个环境变量文件加载进容器。

本节里：

```yaml
env_file:
  - path: ./projects/ai-service/.env
    required: false
```

意思是：

如果本地存在 `projects/ai-service/.env`，就把它加载进 `ai-service` 容器。

如果不存在，也不报错。

为什么要这样？

因为真实 API Key 不应该提交到 GitHub。

你的本机 `.env` 可以有真实密钥。

但仓库里只能放 `.env.example` 或不含密钥的示例文件。

### 4.15 Compose 根目录 .env 和 env_file 的区别

这是新手很容易混淆的地方。

Compose 根目录 `.env` 主要用于替换 `compose.yml` 里的变量。

比如：

```yaml
ports:
  - "${AI_SERVICE_PORT:-8000}:8000"
```

这里的 `AI_SERVICE_PORT` 可以来自仓库根目录 `.env`。

也可以来自命令行：

```bash
docker compose --env-file compose.env.example up
```

而 service 里的 `env_file` 是把变量放进容器内部。

两者不是一回事。

简单说：

Compose 根 `.env`：

给 Compose 文件自己替换变量用。

service `env_file`：

给容器里的应用读取配置用。

### 4.16 为什么新增 compose.env.example

本节新增：

```text
compose.env.example
```

它不含密钥。

它只放端口、模式、日志级别这类安全配置。

你可以：

```bash
docker compose --env-file compose.env.example up
```

或者把它复制成仓库根目录 `.env`：

```bash
cp compose.env.example .env
```

根目录 `.env` 被 `.gitignore` 忽略，不会上传 GitHub。

### 4.17 volumes 是什么

`volumes` 是挂载。

它让容器能读写容器外的数据。

常见有两类：

bind mount。

named volume。

### 4.18 bind mount 是什么

bind mount 是把宿主机目录挂进容器。

比如：

```yaml
volumes:
  - type: bind
    source: ./projects/ai-service
    target: /workspace
```

意思是：

把宿主机上的 `./projects/ai-service` 挂到容器里的 `/workspace`。

容器里改 `/workspace`，宿主机文件也会变。

开发环境常用 bind mount。

因为你改代码后，容器能看到最新文件。

### 4.19 named volume 是什么

named volume 是 Docker 管理的数据卷。

比如：

```yaml
volumes:
  qdrant_storage:
```

它不是某个明确的宿主机路径。

Docker 自己管理它的位置。

它适合存：

Qdrant 数据。

Milvus 数据。

uv 下载缓存。

数据库数据。

named volume 的好处是：

容器删了，数据卷还可以保留。

### 4.20 为什么 uv 缓存要用 named volume

本节 Python 服务用的是：

```yaml
image: ghcr.io/astral-sh/uv:python3.12-bookworm-slim
```

每次容器启动都可能需要同步依赖。

如果没有缓存，每次都重新下载依赖，会很慢。

所以本节挂载：

```yaml
ai_service_uv_cache
java_mock_uv_cache
```

让 uv 的缓存持久化。

### 4.21 为什么不能复用 Windows 的 .venv

你的项目在 Windows 上已经有：

```text
projects/ai-service/.venv
projects/java-mock-service/.venv
```

这些虚拟环境是 Windows 里的。

容器是 Linux 环境。

Windows 的 `.venv` 不能直接给 Linux 容器用。

所以本节 Compose 设置：

```yaml
UV_PROJECT_ENVIRONMENT: /tmp/ai-service-venv
```

意思是：

让 uv 在容器内部的 `/tmp` 创建 Linux 虚拟环境。

不要使用 bind mount 进来的 Windows `.venv`。

这是很重要的工程细节。

### 4.22 networks 是什么

`networks` 是容器网络。

本节定义：

```yaml
networks:
  learning-net:
    driver: bridge
```

所有服务都加入 `learning-net`。

这样它们可以用服务名互相访问。

比如：

```text
ai-service -> java-mock-service:8001
ai-service -> qdrant:6333
ai-service -> milvus-standalone:19530
```

### 4.23 depends_on 是什么

`depends_on` 用来控制启动顺序。

比如：

```yaml
depends_on:
  java-mock-service:
    condition: service_healthy
```

意思是：

`ai-service` 要等 `java-mock-service` 健康检查通过后再启动。

Docker 官方文档提醒：

Compose 默认只等容器 running，不等服务真的 ready。

如果要等 ready，需要配合 `healthcheck` 和 `service_healthy`。

### 4.24 healthcheck 是什么

`healthcheck` 是健康检查。

它会在容器内部执行命令。

如果命令退出码是 0，说明健康。

本节 FastAPI 服务的健康检查是：

```yaml
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2).read()"
```

为什么不用 `curl`？

因为不是所有镜像都有 curl。

Python 镜像一定有 Python。

所以用 Python 标准库做 healthcheck 更稳。

### 4.25 profiles 是什么

profiles 是 Compose 的可选服务分组。

Docker 官方文档说，profiles 可以让某些服务只在指定场景启动。

没有 profiles 的服务默认启动。

有 profiles 的服务需要显式启用。

本节中：

默认启动：

```text
java-mock-service
ai-service
```

启用 Qdrant：

```bash
docker compose --profile qdrant up -d
```

启用 Milvus：

```bash
docker compose --profile milvus up -d
```

为什么这么设计？

因为 Qdrant 和 Milvus 不是每节课都要启动。

Milvus 更重，占内存更多。

默认不启动可以减少资源消耗。

### 4.26 Windows + VMware Ubuntu Docker 的关系

你的 Docker 装在 VMware Ubuntu 里。

这意味着：

Docker 看到的是 Ubuntu 文件系统。

不是 Windows 的 `D:\wendang\java+python+ai`。

所以如果你在 Ubuntu 里执行：

```bash
docker compose up
```

Compose 文件里的：

```yaml
source: ./projects/ai-service
```

指的是 Ubuntu 当前目录下的：

```text
./projects/ai-service
```

不是 Windows 的：

```text
D:/wendang/java+python+ai/projects/ai-service
```

所以要在 Ubuntu 里运行本节 Compose，一般有两种做法：

第一种：

把仓库 clone 到 Ubuntu 里。

第二种：

配置 VMware 共享目录，让 Ubuntu 能访问 Windows 项目目录。

对新手来说，更推荐第一种。

因为 Linux Docker 挂载 Linux 文件系统通常更稳定。

### 4.27 如果仓库还没上传 GitHub 怎么办

本节文件现在先写在 Windows 本地。

如果你想马上在 Ubuntu 里运行，但还没上传 GitHub：

Ubuntu 里 clone 的仓库不会有这些新文件。

解决办法有两个：

1. 先让我帮你上传 GitHub，然后在 Ubuntu 里 `git pull`。
2. 通过 VMware 共享目录或手动复制文件到 Ubuntu。

后续如果你说“帮我上传 GitHub”，我会把这一节和第 33 节一起上传。

### 4.28 Compose 不是 Kubernetes

Compose 适合：

本地开发。

学习。

小型测试环境。

CI 集成测试。

它不是 Kubernetes。

Kubernetes 更适合大型生产环境编排。

但学习顺序上，先学 Compose 很合理。

因为 Compose 更直观。

你先理解服务、网络、端口、环境变量、卷。

以后再学 Kubernetes，会容易很多。

---

## 五、本节主题系统讲解

本节新增两个工程文件：

```text
compose.yml
compose.env.example
```

它们不是单纯为了能跑。

它们也是学习多服务编排的地图。

### 5.1 本节 Compose 的整体结构

`compose.yml` 大致结构是：

```yaml
name: java-python-ai-learning

services:
  java-mock-service:
    ...
  ai-service:
    ...
  qdrant:
    profiles:
      - qdrant
    ...
  milvus-etcd:
    profiles:
      - milvus
    ...
  milvus-minio:
    profiles:
      - milvus
    ...
  milvus-standalone:
    profiles:
      - milvus
    ...

networks:
  learning-net:

volumes:
  ...
```

这就是典型 Compose 结构：

项目名。

服务。

网络。

数据卷。

### 5.2 默认启动哪些服务

默认执行：

```bash
docker compose up -d
```

会启动：

```text
java-mock-service
ai-service
```

不会启动：

```text
qdrant
milvus-etcd
milvus-minio
milvus-standalone
```

因为后面这些有 profile。

这样设计是为了让最小学习环境更轻。

### 5.3 启动 Qdrant

如果本节要同时启动 Qdrant：

```bash
docker compose --profile qdrant up -d
```

启动后访问：

```bash
curl http://localhost:6333
```

注意：

如果你 Ubuntu 里已经有之前手动启动的 `qdrant` 容器，并且它占用了 6333 端口，Compose 启动会失败。

这不是代码错。

这是端口冲突。

你可以选择：

停止旧容器。

或者不要启用本节 `qdrant` profile。

### 5.4 启动 Milvus

如果要启动 Milvus：

```bash
docker compose --profile milvus up -d
```

它会启动：

```text
milvus-etcd
milvus-minio
milvus-standalone
```

端口：

```text
19530  Milvus gRPC
9091   Milvus Web / health
9000   MinIO API
9001   MinIO Console
```

注意：

Milvus 比 Qdrant 重。

你的 VMware Ubuntu 之前已经成功运行过 Milvus，但如果旧 Milvus 还在运行，也会有端口冲突。

### 5.5 ai-service 怎么访问 java-mock-service

在宿主机上，你访问 Java mock 服务可能是：

```text
http://127.0.0.1:8001
```

但在 Compose 网络里，`ai-service` 访问它是：

```text
http://java-mock-service:8001
```

所以 Compose 里设置：

```yaml
JAVA_MOCK_SERVICE_BASE_URL: http://java-mock-service:8001
```

这个变量会覆盖 `projects/ai-service/.env` 里的本机地址。

这是容器网络里非常重要的概念。

### 5.6 ai-service 怎么访问 Qdrant 和 Milvus

如果启用了 qdrant profile：

```yaml
QDRANT_BASE_URL: http://qdrant:6333
```

如果启用了 milvus profile：

```yaml
MILVUS_URI: http://milvus-standalone:19530
```

这些都是服务名。

不是 IP。

不是 localhost。

服务名由 Compose 网络解析。

### 5.7 为什么 Qdrant 和 Milvus 不默认启动

原因有三个。

第一：

不是每节课都用向量库。

第二：

Milvus 占用资源更多。

第三：

你之前已经单独启动过 Qdrant 和 Milvus。

如果默认再启动一套，容易端口冲突。

所以本节用 profiles。

需要时再启用。

### 5.8 为什么没有写 Dockerfile

本节没有新增 Dockerfile。

因为当前重点是 Compose 编排。

我们用：

```text
ghcr.io/astral-sh/uv:python3.12-bookworm-slim
```

作为 Python 服务基础镜像。

通过 bind mount 挂载项目代码。

启动时执行 `uv sync` 和 `uv run uvicorn`。

这更适合本地开发。

以后学部署时，再把应用打包成固定镜像。

### 5.9 本节 Compose 的学习版和生产版差距

本节是学习版 Compose。

它适合：

本地开发。

理解服务编排。

快速启动依赖。

它还不是生产版部署。

生产环境还需要考虑：

镜像构建。

镜像版本管理。

密钥管理。

资源限制。

日志采集。

监控。

备份。

安全网络。

CI/CD。

滚动发布。

### 5.10 本节运行命令地图

在有 Docker 的 Ubuntu 里，如果仓库已经包含本节文件，可以这样操作。

进入仓库：

```bash
cd ~/java-python-ai
```

检查 Compose 渲染结果：

```bash
docker compose --env-file compose.env.example config
```

启动默认服务：

```bash
docker compose --env-file compose.env.example up -d
```

查看状态：

```bash
docker compose ps
```

看日志：

```bash
docker compose logs -f ai-service
docker compose logs -f java-mock-service
```

访问健康检查：

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8001/health
curl http://localhost:8001/ready
```

启动 Qdrant：

```bash
docker compose --env-file compose.env.example --profile qdrant up -d
```

启动 Milvus：

```bash
docker compose --env-file compose.env.example --profile milvus up -d
```

停止服务但保留数据卷：

```bash
docker compose down
```

停止并删除数据卷：

```bash
docker compose down -v
```

注意：

`down -v` 会删除 named volumes。

Qdrant 和 Milvus 数据也会删。

新手不要随便执行。

---

## 六、本节代码讲解

本节主要新增：

```text
compose.yml
compose.env.example
```

### 6.1 name

```yaml
name: java-python-ai-learning
```

这是 Compose 项目名。

它会影响容器、网络、卷的命名。

设置明确项目名的好处是：

看到容器名时，知道它属于哪个项目。

### 6.2 java-mock-service

```yaml
java-mock-service:
  image: ghcr.io/astral-sh/uv:python3.12-bookworm-slim
  working_dir: /workspace
```

这个服务用 Python + uv 镜像。

`working_dir` 表示容器进入后默认工作目录是 `/workspace`。

项目代码通过 bind mount 挂进去。

### 6.3 java-mock-service command

```yaml
command: >
  sh -lc "uv sync --frozen &&
  uv run uvicorn app.main:app --host 0.0.0.0 --port 8001"
```

它先执行：

```bash
uv sync --frozen
```

再执行：

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

`--frozen` 的意思是：

按锁文件同步依赖，不随意更新依赖版本。

### 6.4 ai-service env_file

```yaml
env_file:
  - path: ./projects/ai-service/.env
    required: false
```

这让容器可以读取你本机的 AI 服务配置。

比如真实模型 API Key。

但 `required: false` 表示没有这个文件也可以启动。

默认模式是：

```text
rule_based
```

不会真实调用模型。

### 6.5 ai-service environment 覆盖

```yaml
JAVA_MOCK_SERVICE_BASE_URL: http://java-mock-service:8001
QDRANT_BASE_URL: http://qdrant:6333
MILVUS_URI: http://milvus-standalone:19530
```

这些值会覆盖 `.env` 里对应配置。

原因是：

容器里不能用宿主机的 `127.0.0.1` 访问另一个容器。

要用服务名。

### 6.6 healthcheck

```yaml
healthcheck:
  test:
    - CMD
    - python
    - -c
    - "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2).read()"
```

这段健康检查在容器内部执行。

它访问容器自己的 `/ready`。

这里用 `/ready`，是因为 Compose healthcheck 不只想知道进程是否还活着，还想知道服务是否已经准备好接收流量。下一节会专门区分 `/health` 和 `/ready`。

如果能访问成功，容器就是 healthy。

### 6.7 qdrant profile

```yaml
qdrant:
  image: qdrant/qdrant:v1.18.2
  profiles:
    - qdrant
```

这表示 Qdrant 不是默认服务。

只有启用 qdrant profile 时才启动。

### 6.8 milvus 三个服务

Milvus standalone 不是一个简单单容器服务。

它通常依赖：

```text
etcd
MinIO
Milvus standalone
```

所以 Compose 里是三个服务：

```text
milvus-etcd
milvus-minio
milvus-standalone
```

这和你之前在 Ubuntu 里看到的容器是对应的。

### 6.9 depends_on service_healthy

```yaml
depends_on:
  milvus-etcd:
    condition: service_healthy
  milvus-minio:
    condition: service_healthy
```

意思是：

Milvus standalone 要等 etcd 和 MinIO 健康后再启动。

这比单纯启动顺序更可靠。

### 6.10 compose.env.example

```text
AI_SERVICE_PORT=8000
JAVA_MOCK_SERVICE_PORT=8001
QDRANT_HTTP_PORT=6333
```

这个文件只放安全示例配置。

不放密钥。

如果你要改端口，比如本机 6333 已经被占用，可以复制为 `.env` 后改：

```text
QDRANT_HTTP_PORT=16333
```

然后宿主机访问 Qdrant 就用：

```text
http://localhost:16333
```

容器内部仍然用：

```text
http://qdrant:6333
```

---

## 七、本节实践注意事项

### 7.1 需要打开 VMware 吗

当前 Windows 环境没有 Docker 命令。

所以真实运行 Compose 时需要打开 VMware Ubuntu。

但本节文件编写和 Python 测试可以在 Windows 完成。

### 7.2 Ubuntu 里需要有仓库

如果你要在 Ubuntu 里运行：

```bash
docker compose up
```

Ubuntu 里必须有本仓库文件。

例如：

```bash
cd ~
git clone https://github.com/panpan330/agent-hello.git java-python-ai
cd java-python-ai
```

如果本节还没上传 GitHub，Ubuntu clone 下来的仓库不会有本节文件。

### 7.3 不要同时启动两套 Qdrant/Milvus

你之前已经在 Ubuntu Docker 里启动过 Qdrant 和 Milvus。

如果它们还在运行，本节 Compose 再启动 qdrant 或 milvus profile，可能端口冲突：

```text
6333
6334
19530
9091
9000
9001
```

遇到端口冲突，不要慌。

先查看：

```bash
docker ps
```

再决定是停止旧容器，还是不启用本节 profile。

### 7.4 不要随便 down -v

```bash
docker compose down
```

会停止并删除容器、默认网络。

通常不会删除 named volume。

```bash
docker compose down -v
```

会额外删除数据卷。

这可能删除 Qdrant/Milvus 数据。

所以不要随便加 `-v`。

### 7.5 如果镜像拉取慢

你之前已经遇到过 Qdrant 拉取慢。

Compose 也会拉镜像。

如果慢，原因可能是：

网络到镜像仓库慢。

镜像较大。

Milvus 相关镜像多。

解决方向包括：

先单独 pull。

换网络。

配置镜像加速。

优先只启动默认服务，不启用 Milvus profile。

---

## 八、把本节讲给别人时可以这样说

如果别人问：

Docker Compose 是什么？

你可以回答：

Docker Compose 是用一个 YAML 文件定义和运行多容器应用的工具。它能同时管理服务、网络、端口、环境变量和数据卷，适合本地开发和多服务联调。

如果别人问：

Docker 和 Docker Compose 有什么区别？

你可以回答：

Docker 更偏单容器操作，Compose 更偏一组服务的编排。一个服务可以用 docker run 启动，但多个服务之间的网络、端口、卷和启动顺序用 Compose 管理更清晰。

如果别人问：

容器里为什么不能用 127.0.0.1 访问另一个容器？

你可以回答：

容器里的 127.0.0.1 指的是容器自己，不是宿主机，也不是别的容器。同一个 Compose 网络里的容器应该用服务名访问，比如 `http://java-mock-service:8001`。

如果别人问：

env_file 和根目录 .env 有什么区别？

你可以回答：

根目录 `.env` 主要给 Compose 文件做变量替换，比如端口 `${AI_SERVICE_PORT}`。service 里的 `env_file` 是把变量注入容器内部，让应用读取。两者用途不同。

如果别人问：

为什么 Qdrant 和 Milvus 用 profiles？

你可以回答：

因为它们不是每次学习都需要启动，而且 Milvus 比较重。用 profiles 可以让默认环境只启动核心服务，需要向量库时再显式启用。

如果别人问：

Windows 项目和 VMware Ubuntu Docker 有什么关系？

你可以回答：

Docker 在 Ubuntu 里运行时，Compose 的 bind mount 路径是 Ubuntu 里的路径，不是 Windows 的 `D:\...`。要在 Ubuntu 里运行 Compose，仓库要在 Ubuntu 文件系统里，或者配置 VMware 共享目录。

---

## 九、本节练习

### 练习 1

解释 Docker Compose 解决什么问题。

参考答案：

Docker Compose 解决多容器应用的本地编排问题。

它用一个 YAML 文件描述多个服务、端口、环境变量、网络和数据卷，让开发者可以用一组命令启动、停止和查看整个应用栈。

### 练习 2

解释 `8000:8000` 的含义。

参考答案：

左边的 8000 是宿主机端口。

右边的 8000 是容器端口。

访问宿主机 `localhost:8000` 会转发到容器内部的 8000 端口。

### 练习 3

为什么 `ai-service` 容器访问 `java-mock-service` 不能用 `127.0.0.1:8001`？

参考答案：

因为容器里的 `127.0.0.1` 指的是当前容器自己。

`java-mock-service` 在另一个容器里。

同一个 Compose 网络里应该用服务名访问：

```text
http://java-mock-service:8001
```

### 练习 4

解释 bind mount 和 named volume 的区别。

参考答案：

bind mount 是把宿主机明确目录挂进容器，适合开发时同步代码。

named volume 是 Docker 管理的数据卷，适合保存数据库、向量库、缓存等需要持久化的数据。

### 练习 5

为什么本节设置 `UV_PROJECT_ENVIRONMENT=/tmp/ai-service-venv`？

参考答案：

因为项目目录里可能有 Windows 的 `.venv`。

Linux 容器不能直接复用 Windows 虚拟环境。

设置 `UV_PROJECT_ENVIRONMENT` 可以让 uv 在容器内部创建自己的 Linux 虚拟环境。

### 练习 6

为什么不能把真实 API Key 写进 `compose.yml`？

参考答案：

因为 `compose.yml` 会提交到 GitHub。

真实 API Key 如果写进去就会泄漏。

正确做法是把密钥放在本地 `.env` 或专门的密钥管理系统里，仓库里只提交示例文件。

### 练习 7

为什么本节 Qdrant 和 Milvus 不默认启动？

参考答案：

因为它们不是每节课都需要，而且 Milvus 比较重。

另外用户之前可能已经单独启动过 Qdrant 或 Milvus，如果默认启动会更容易端口冲突。

所以用 profiles，需要时再启动。

### 练习 8

解释 `docker compose down` 和 `docker compose down -v` 的区别。

参考答案：

`docker compose down` 会停止并删除容器和默认网络，通常保留 named volumes。

`docker compose down -v` 会额外删除数据卷，可能导致 Qdrant/Milvus 数据丢失。

---

## 十、自测题

### 自测 1

Docker Compose 是不是只能用于生产环境？

答案：

不是。

Compose 很常用于本地开发、学习、测试和 CI。

生产环境也可以用，但复杂生产部署通常还会考虑 Kubernetes、服务网格、云平台等方案。

### 自测 2

`services` 下面的每一项通常表示什么？

答案：

通常表示一个服务，也可以理解为一个容器模板。

Compose 根据 service 配置创建和运行容器。

### 自测 3

Compose 文件里的 `image` 是正在运行的容器吗？

答案：

不是。

`image` 是镜像，是容器的模板。

运行起来的实例才是 container。

### 自测 4

为什么 FastAPI 在容器里要监听 `0.0.0.0`？

答案：

因为如果只监听 `127.0.0.1`，服务只在容器内部可访问。

监听 `0.0.0.0` 才能通过端口映射让宿主机访问。

### 自测 5

`depends_on` 默认会等待服务完全 ready 吗？

答案：

不会。

Docker 官方文档说明，Compose 默认只等容器 running，不等服务 ready。

如果要等 ready，需要配合 `healthcheck` 和 `condition: service_healthy`。

### 自测 6

profiles 的作用是什么？

答案：

profiles 用来把某些服务设为可选启动。

没有 profile 的服务默认启动。

有 profile 的服务只有显式启用时才启动。

### 自测 7

Docker 在 VMware Ubuntu 里时，Compose 的 `./projects/ai-service` 指的是 Windows 目录吗？

答案：

不是。

它指的是 Ubuntu 当前工作目录下的相对路径。

如果要在 Ubuntu 里运行 Compose，仓库也需要在 Ubuntu 能访问的位置。

### 自测 8

本节 `compose.env.example` 能不能放真实 API Key？

答案：

不能。

它是会提交到仓库的示例文件，只能放不敏感的示例配置。

真实 API Key 应该放在本地 `.env`，并确保不提交。

### 自测 9

如果启动 Qdrant profile 时提示 6333 端口被占用，最可能是什么原因？

答案：

很可能是之前已经有一个 Qdrant 容器或其他进程占用了 6333。

应该先用 `docker ps` 查看，再决定停止旧容器或改端口。

### 自测 10

本节是否已经在 Windows 环境真实运行了 Docker Compose？

答案：

没有。

当前 Windows 环境没有 `docker` 命令。

你的 Docker 在 VMware Ubuntu 里，真实运行 Compose 需要打开 Ubuntu 虚拟机。

---

## 十一、本节小结

本节从生产稳定性策略转到了本地运行环境编排。

你学了：

Docker 和 Docker Compose 的区别。

Compose 文件的基本结构。

services、image、command、ports、environment、env_file、volumes、networks、depends_on、healthcheck、profiles。

你也学了：

容器里的 localhost 是自己。

容器之间要用服务名访问。

Windows `.venv` 不能给 Linux 容器用。

Docker 在 Ubuntu 里时，Compose 挂载的是 Ubuntu 路径。

真实密钥不能写进 Compose。

本节新增的 `compose.yml` 是一个学习版本地编排文件。

它默认启动：

```text
java-mock-service
ai-service
```

需要时可以启用：

```text
qdrant profile
milvus profile
```

下一步如果你想实机验证，就需要打开 VMware Ubuntu。

---

## 十二、下一节学什么

下一节是阶段 6 第 35 节：

```text
health check、readiness 和 CI 自动回归
```

它会接着本节继续学：

1. health check 是什么。
2. readiness 是什么。
3. liveness 和 readiness 的区别。
4. Compose healthcheck 和应用 `/health`、`/ready` 的关系。
5. 为什么 CI 要自动跑测试。
6. 如何用脚本或配置让项目具备基础自动回归能力。

下一节不一定需要一开始就打开 VMware。

如果要验证 Compose healthcheck，我会明确告诉你需要开虚拟机。
