#!/bin/bash
# ============================================
# 部署包打包脚本
# ============================================
# 功能：将项目打包为 tar.gz 部署包
# 使用方法：./package_deployment.sh
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Indonesia 项目部署包打包工具${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 获取当前版本信息
VERSION=$(git log -1 --pretty=format:'%h' --abbrev-commit)
VERSION_DATE=$(git log -1 --pretty=format:'%ad' --date=format:'%Y%m%d_%H%M%S')
VERSION_NAME="v5.0_${VERSION_DATE}_${VERSION}"

echo -e "${YELLOW}版本信息：${NC}"
echo -e "  Git Commit: ${VERSION}"
echo -e "  版本名称: ${VERSION_NAME}"
echo ""

# 定义输出文件名
OUTPUT_FILE="indonesia_search_${VERSION_NAME}.tar.gz"
OUTPUT_DIR="deployment_packages"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

echo -e "${YELLOW}步骤 1/5: 清理临时文件...${NC}"
# 删除旧的 __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ 临时文件已清理${NC}"
echo ""

echo -e "${YELLOW}步骤 2/5: 复制项目文件到临时目录...${NC}"
TEMP_DIR=$(mktemp -d)
echo "临时目录: $TEMP_DIR"

# 使用 rsync 复制文件，排除不需要的文件
rsync -av \
    --exclude-from="$PROJECT_ROOT/deploy_exclude.txt" \
    --exclude=".git" \
    --exclude="deployment_packages" \
    --exclude="$OUTPUT_DIR" \
    --exclude="*.tar.gz" \
    "$PROJECT_ROOT/" "$TEMP_DIR/indonesia_search/" \
    | grep -v "/$" || true

echo -e "${GREEN}✓ 文件复制完成${NC}"
echo ""

echo -e "${YELLOW}步骤 3/5: 创建版本信息文件...${NC}"
cat > "$TEMP_DIR/indonesia_search/VERSION.txt" << EOF
===========================================
Indonesia 教育搜索系统
===========================================
版本: ${VERSION_NAME}
Git Commit: ${VERSION}
打包时间: $(date '+%Y-%m-%d %H:%M:%S')
打包机器: $(hostname)
===========================================
EOF

echo -e "${GREEN}✓ 版本信息已创建${NC}"
echo ""

echo -e "${YELLOW}步骤 4/5: 打包为 tar.gz...${NC}"
cd "$TEMP_DIR"
tar -czf "$PROJECT_ROOT/$OUTPUT_DIR/$OUTPUT_FILE" indonesia_search/
FILE_SIZE=$(du -h "$PROJECT_ROOT/$OUTPUT_DIR/$OUTPUT_FILE" | cut -f1)
echo -e "${GREEN}✓ 打包完成: ${OUTPUT_FILE} (${FILE_SIZE})${NC}"
echo ""

echo -e "${YELLOW}步骤 5/5: 生成校验和...${NC}"
cd "$PROJECT_ROOT/$OUTPUT_DIR"
sha256sum "$OUTPUT_FILE" > "$OUTPUT_FILE.sha256"
echo -e "${GREEN}✓ SHA256 校验和已生成${NC}"
echo ""

# 清理临时目录
rm -rf "$TEMP_DIR"

# 显示结果
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  打包完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}部署包位置：${NC}"
echo -e "  ${OUTPUT_DIR}/${OUTPUT_FILE}"
echo ""
echo -e "${YELLOW}校验和：${NC}"
cat "$OUTPUT_FILE.sha256"
echo ""
echo -e "${YELLOW}文件大小：${NC} ${FILE_SIZE}"
echo ""
echo -e "${YELLOW}后续步骤：${NC}"
echo -e "  1. 上传到服务器："
echo -e "     scp ${OUTPUT_DIR}/${OUTPUT_FILE} user@server:/path/to/deploy/"
echo ""
echo -e "  2. 在服务器上解压："
echo -e "     tar -xzf ${OUTPUT_FILE}"
echo ""
echo -e "  3. 阅读 DEPLOYMENT.md 完成部署"
echo ""
echo -e "${GREEN}✓ 所有步骤完成！${NC}"
