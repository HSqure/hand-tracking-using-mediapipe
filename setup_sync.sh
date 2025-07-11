#!/bin/bash

echo "🚀 多设备Git同步自动设置脚本"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查当前Git状态
echo -e "${BLUE}📋 检查当前Git状态...${NC}"
git status

echo -e "\n${YELLOW}⚠️  当前问题分析：${NC}"
echo "1. 您没有推送权限到原仓库"
echo "2. 需要配置自己的远程仓库"
echo "3. 需要设置认证信息"

echo -e "\n${BLUE}🔧 请选择解决方案：${NC}"
echo "1) Fork原仓库到我的GitHub账户（推荐）"
echo "2) 创建全新的仓库"
echo "3) 配置SSH密钥认证"
echo "4) 配置GitHub Token认证"
echo "5) 显示完整同步指南"

read -p "请输入选项 (1-5): " choice

case $choice in
  1)
    echo -e "\n${GREEN}📝 Fork仓库设置步骤：${NC}"
    echo "1. 在浏览器中打开："
    echo "   https://github.com/Sousannah/hand-tracking-using-mediapipe"
    echo "2. 点击右上角的 'Fork' 按钮"
    echo "3. Fork到您的账户后，回来输入您的用户名"
    
    read -p "请输入您的GitHub用户名: " username
    
    if [ ! -z "$username" ]; then
      echo -e "\n${BLUE}🔄 更新远程仓库配置...${NC}"
      git remote add upstream https://github.com/Sousannah/hand-tracking-using-mediapipe.git
      git remote set-url origin https://github.com/$username/hand-tracking-using-mediapipe.git
      
      echo -e "${GREEN}✅ 远程仓库配置完成！${NC}"
      echo "现在可以执行："
      echo "git push origin main"
    fi
    ;;
    
  2)
    read -p "请输入您的GitHub用户名: " username
    read -p "请输入新仓库名称: " reponame
    
    if [ ! -z "$username" ] && [ ! -z "$reponame" ]; then
      echo -e "\n${BLUE}🔄 更新到新仓库...${NC}"
      git remote set-url origin https://github.com/$username/$reponame.git
      
      echo -e "${YELLOW}📋 请先在GitHub创建仓库：${NC}"
      echo "https://github.com/new"
      echo "仓库名: $reponame"
      
      read -p "创建完成后按Enter继续..." 
      echo "执行推送命令："
      echo "git push -u origin main"
    fi
    ;;
    
  3)
    echo -e "\n${GREEN}🔑 SSH密钥设置步骤：${NC}"
    
    read -p "请输入您的邮箱: " email
    
    if [ ! -z "$email" ]; then
      echo -e "${BLUE}生成SSH密钥...${NC}"
      ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""
      
      echo -e "${BLUE}启动ssh-agent...${NC}"
      eval "$(ssh-agent -s)"
      ssh-add ~/.ssh/id_ed25519
      
      echo -e "\n${YELLOW}📋 请复制以下公钥到GitHub：${NC}"
      cat ~/.ssh/id_ed25519.pub
      
      echo -e "\n${GREEN}📝 添加步骤：${NC}"
      echo "1. 打开 https://github.com/settings/ssh"
      echo "2. 点击 'New SSH key'"
      echo "3. 粘贴上面的公钥内容"
      echo "4. 点击 'Add SSH key'"
      
      read -p "添加完成后按Enter继续..." 
      
      # 更新仓库URL为SSH格式
      current_url=$(git remote get-url origin)
      if [[ $current_url == https://github.com/* ]]; then
        ssh_url=$(echo $current_url | sed 's/https:\/\/github.com\//git@github.com:/')
        git remote set-url origin $ssh_url
        echo -e "${GREEN}✅ 已更新为SSH URL${NC}"
      fi
    fi
    ;;
    
  4)
    echo -e "\n${GREEN}🎫 GitHub Token设置步骤：${NC}"
    echo "1. 打开 https://github.com/settings/tokens"
    echo "2. 点击 'Generate new token (classic)'"
    echo "3. 选择权限：repo (完整仓库权限)"
    echo "4. 点击 'Generate token'"
    echo "5. 复制生成的token"
    
    read -p "设置完成后按Enter继续..." 
    
    git config --global credential.helper store
    
    echo -e "${YELLOW}💡 下次推送时输入：${NC}"
    echo "Username: 您的GitHub用户名"
    echo "Password: 刚才生成的token（不是GitHub密码）"
    ;;
    
  5)
    echo -e "\n${GREEN}📖 打开完整同步指南...${NC}"
    if command -v code &> /dev/null; then
      code SYNC_GUIDE.md
    elif command -v nano &> /dev/null; then
      nano SYNC_GUIDE.md
    else
      cat SYNC_GUIDE.md
    fi
    ;;
    
  *)
    echo -e "${RED}❌ 无效选项${NC}"
    ;;
esac

echo -e "\n${GREEN}🎯 接下来的标准工作流程：${NC}"
echo "1. git add .                    # 添加所有更改"
echo "2. git commit -m \"描述\"       # 提交更改"  
echo "3. git push origin main         # 推送到远程"
echo "4. 在另一台电脑：git pull origin main  # 同步最新"

echo -e "\n${BLUE}📱 多设备同步核心原则：${NC}"
echo "✅ 开始工作前：git pull"
echo "✅ 结束工作后：git push" 
echo "✅ 频繁提交，小步快跑"
echo "✅ 遇到冲突不要慌，按指南操作"

echo -e "\n${GREEN}🚀 设置完成！查看 SYNC_GUIDE.md 获取详细指南${NC}" 