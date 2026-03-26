# 使用微软官方维护的 Miniconda 镜像作为底层
FROM mcr.microsoft.com/devcontainers/miniconda:0-3

# 安装处理音频和模型所需的底层系统库
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    ffmpeg \
    libsndfile-dev \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*