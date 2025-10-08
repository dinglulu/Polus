# README 

本项目包含一个打包好的 Docker 镜像 `polus_v1.tar.gz`，用于运行 POLUS 应用。以下是详细使用步骤。

------

## 1. 解压项目文件

首先解压 `POLUS.zip`：

```
unzip POLUS.zip
cd POLUS
```

此时目录下应包含：

- `polus_v1.tar.gz`（Docker 镜像文件）
- `files/`、`media/`、`upload/`、`sessions/`（挂载目录）
- 其他项目代码文件

------

## 2. 导入 Docker 镜像

将镜像导入本地 Docker：

```
gunzip -c polus_v1.tar.gz | docker load
```

导入完成后，可以通过以下命令确认：

```
docker images | grep polus
```

能看到 `polus:v1`。

------

## 3. 启动容器

### 3.1运行以下命令启动容器：

```
docker run -d \
  --name polus-app \
  -p 8045:8045 \
  -v $(pwd)/files:/app/files \
  -v $(pwd)/media:/app/media \
  -v $(pwd)/upload:/app/upload \
  -v $(pwd)/sessions:/app/sessions \
  -e TZ=Asia/Shanghai \
  -w /app \
  --restart unless-stopped \
  polus:v1 \
  bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate POLUS && python manage.py runserver 0.0.0.0:8045"
```

说明：

- `-p 8045:8045`：将容器内的 8045 端口映射到宿主机。
- `-v $(pwd)/xxx:/app/xxx`：挂载当前目录下的 `files/media/upload/sessions`，确保数据不会随容器删除而丢失。
- `--restart unless-stopped`：容器会在系统重启时自动启动。
- `bash -c "source ... && conda activate POLUS ..."`：保证 conda 环境正确激活后运行 Django。

------

### 3.2 docker-compose.yml

启动：

```
docker compose up -d
```

查看运行状态：

```
docker compose ps
```

## 4. 验证运行

查看容器状态：

```
docker ps
```

查看日志：

```
docker logs -f polus-app
```

如果启动成功，你应该看到类似日志：

------

## 5. 访问服务

开放端口8045

在宿主机上访问：

```
http://localhost:8045/
```

如果在远程服务器运行，则访问：

```
http://<服务器IP>:8045/
```