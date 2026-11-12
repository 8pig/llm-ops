#!/usr/bin/env bash
# ============================================================
# 拉取 LLMOps 依赖镜像（postgres / weaviate）
#
# 用法（在目标机器上，仓库任意目录）：
#   bash docker/pull-images.sh
#
# 说明：
#   1. 依次尝试华为云 / DaoCloud / 1ms / Docker Hub 四个源；
#   2. 从镜像站拉到的镜像会自动重新打上 compose 需要的原始标签；
#   3. 标签必须与 docker/docker-compose.yaml 完全一致，不要改。
# ============================================================
set -euo pipefail

# 需要拉取的镜像，按需增删（redis 也在这里，注释掉即可）
IMAGES=(
  "postgres:15-alpine"
  "semitechnologies/weaviate:1.35.3"
  # "redis:6-alpine"
)

# 镜像源前缀，按顺序尝试；空字符串代表 Docker Hub 官方源
MIRRORS=(
  "swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/"
  "docker.m.daocloud.io/"
  "docker.1ms.run/"
  ""
)

# 单次拉取超时（秒），网络慢可以调大：PULL_TIMEOUT=600 bash docker/pull-images.sh
PULL_TIMEOUT="${PULL_TIMEOUT:-180}"

# 根据源前缀拼出镜像地址：官方镜像需要补 library/
build_ref() {
  local prefix="$1"
  local repo="${2%:*}"
  local tag="${2##*:}"

  if [[ -z "$prefix" ]]; then
    echo "$2"
  elif [[ "$repo" == *"/"* ]]; then
    echo "${prefix}${repo}:${tag}"
  else
    echo "${prefix}library/${repo}:${tag}"
  fi
}

pull_image() {
  local image="$1"

  for prefix in "${MIRRORS[@]}"; do
    local ref
    ref="$(build_ref "$prefix" "$image")"

    echo ">>> 尝试拉取: $ref"
    if timeout "$PULL_TIMEOUT" docker pull "$ref"; then
      if [[ "$ref" != "$image" ]]; then
        docker tag "$ref" "$image"
        echo ">>> 已重新打标签: $ref -> $image"
      fi
      echo "OK: $image"
      return 0
    fi
    echo "!!! 该源失败，换下一个"
  done

  echo "ERROR: 所有源都无法拉取 $image" >&2
  return 1
}

main() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: 未找到 docker 命令" >&2
    exit 1
  fi

  echo "架构: $(uname -m)"
  echo "开始拉取 ${#IMAGES[@]} 个镜像"
  echo

  for image in "${IMAGES[@]}"; do
    pull_image "$image"
    docker image inspect "$image" --format '    本地镜像: {{.RepoTags}} {{.Os}}/{{.Architecture}}'
    echo
  done

  echo "全部完成。可以直接执行:"
  echo "  cd docker && docker compose up -d llmops-db llmops-weaviate"
}

main "$@"
