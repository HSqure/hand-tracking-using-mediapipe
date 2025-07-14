#!/bin/bash

# =================================================================
#  Git 同步与更新自动化脚本
# =================================================================
#
#  一键处理日常的 Git 推送、拉取和上游同步任务。
#
# =================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 帮助信息
function show_usage {
  echo -e "${BLUE}用法: ./sync.sh [命令] [参数]${NC}"
  echo ""
  echo -e "${GREEN}命令:${NC}"
  echo -e "  ${YELLOW}push \"提交信息\"${NC}   - 将所有本地修改提交并推送到远程仓库 (origin/main)。"
  echo -e "                       提交信息必须用双引号括起来。"
  echo -e "  ${YELLOW}pull${NC}              - 从您的远程仓库 (origin/main) 拉取最新更新。"
  echo -e "  ${YELLOW}upstream-sync${NC}   - 从原始开发者仓库 (upstream/main) 同步更新。"
  echo -e "  ${YELLOW}help${NC}              - 显示此帮助信息。"
  echo ""
  echo -e "${BLUE}示例:${NC}"
  echo -e "  ./sync.sh push \"修复了摄像头bug\""
  echo -e "  ./sync.sh pull"
  echo ""
}

# 检查是否在Git仓库中
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}错误: 当前目录不是一个Git仓库。${NC}"
    exit 1
fi


# 主逻辑
case "$1" in
  push)
    # 检查是否提供了提交信息
    if [ -z "$2" ]; then
      echo -e "${RED}错误: 'push' 命令需要一个提交信息作为参数。${NC}"
      show_usage
      exit 1
    fi

    echo -e "${BLUE}======= 开始执行推送流程 =======${NC}"

    echo -e "\n${YELLOW}第一步: 检查远程更新...${NC}"
    git pull origin main
    if [ $? -ne 0 ]; then
        echo -e "${RED}拉取远程更新时遇到冲突或错误，请先手动解决后再运行此脚本。${NC}"
        exit 1
    fi

    echo -e "\n${YELLOW}第二步: 添加所有本地更改...${NC}"
    git add .
    echo -e "✅ 添加完成。"

    echo -e "\n${YELLOW}第三步: 提交更改...${NC}"
    git commit -m "$2"
    if [ $? -ne 0 ]; then
        echo -e "${RED}提交失败。可能是没有需要提交的更改，或者有其他错误。${NC}"
        exit 1
    fi
    echo -e "✅ 提交完成。"

    echo -e "\n${YELLOW}第四步: 推送到远程仓库 (origin/main)...${NC}"
    git push origin main
    if [ $? -ne 0 ]; then
        echo -e "${RED}推送失败，请检查网络和权限。${NC}"
        exit 1
    fi
    echo -e "✅ 推送完成。"

    echo -e "\n${GREEN}🚀 同步成功！您的代码已更新至GitHub。${NC}"
    ;;

  pull)
    echo -e "${BLUE}======= 开始从 origin 拉取更新 =======${NC}"
    git pull origin main
    if [ $? -ne 0 ]; then
        echo -e "${RED}拉取失败。请检查网络、权限或手动解决冲突。${NC}"
        exit 1
    fi
    echo -e "\n${GREEN}✅ 更新完成！本地仓库已是最新版本。${NC}"
    ;;

  upstream-sync)
    echo -e "${BLUE}======= 开始从 upstream 同步更新 =======${NC}"

    echo -e "\n${YELLOW}第一步: 从上游仓库 (upstream) 获取最新数据...${NC}"
    git fetch upstream
    if [ $? -ne 0 ]; then
        echo -e "${RED}获取上游仓库数据失败。${NC}"
        exit 1
    fi
    echo -e "✅ 获取完成。"

    echo -e "\n${YELLOW}第二步: 合并上游仓库的 'main' 分支...${NC}"
    git merge upstream/main
    if [ $? -ne 0 ]; then
        echo -e "${RED}合并失败。请手动解决冲突。${NC}"
        exit 1
    fi
    echo -e "✅ 合并完成。"

    echo -e "\n${YELLOW}第三步: 将同步后的代码推送到您的远程仓库 (origin)...${NC}"
    git push origin main
     if [ $? -ne 0 ]; then
        echo -e "${RED}推送失败。${NC}"
        exit 1
    fi
    echo -e "✅ 推送完成。"

    echo -e "\n${GREEN}🎉 与上游同步成功！${NC}"
    ;;

  help|--help|-h|*)
    show_usage
    ;;
esac 