#!/bin/bash

echo "🔄 从原始仓库同步最新更新"
echo "==============================="

# 获取原始仓库的最新更改
echo "📥 获取上游仓库更新..."
git fetch upstream

# 切换到main分支
echo "🔀 切换到main分支..."
git checkout main

# 合并上游更改
echo "🔗 合并上游更改..."
git merge upstream/main

# 推送到自己的fork
echo "📤 推送到自己的fork..."
git push origin main

echo "✅ 同步完成！"
echo ""
echo "💡 如果遇到冲突，请："
echo "1. 手动解决冲突文件"
echo "2. git add 解决后的文件"
echo "3. git commit -m '解决合并冲突'"
echo "4. git push origin main" 