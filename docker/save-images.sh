#!/usr/bin/env bash
# ============================================================
# 在本机（已有镜像的机器）导出 postgres / weaviate 镜像，
# 适合目标机器完全连不上 Docker Hub 和国内镜像站的情况。
#
# 用法：
#   bash docker/save-images.sh                 # 生成 llmops-deps.tar.gz
#   bash docker/save-images.sh /tmp/deps.tar.gz
#
# 目标机器导入：
#   gunzip -c llmops-deps.tar.gz | docker load
# ============================================================
set -euo pipefail

OUT="${1:-llmops-deps.tar.gz}"

IMAGES=(
  "postgres:15-alpine"
  "semitechnologies/weaviate:1.35.3"
  # "redis:6-alpine"
)

for image in "${IMAGES[@]}"; do
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    echo "ERROR: 本机缺少 $image，请先执行 bash docker/pull-images.sh" >&2
    exit 1
  fi
done

echo ">>> 导出到 $OUT"
docker save "${IMAGES[@]}" | gzip -1 > "$OUT"

echo "完成: $OUT ($(du -h "$OUT" | cut -f1))"
echo "拷贝到目标机器后执行:"
echo "  gunzip -c $(basename "$OUT") | docker load"
