# 🔄 多设备Git同步完整指南

## 📋 目录
1. [初始设置](#初始设置)
2. [权限配置](#权限配置)
3. [日常工作流程](#日常工作流程)
4. [冲突解决](#冲突解决)
5. [最佳实践](#最佳实践)
6. [紧急恢复](#紧急恢复)

---

## 🚀 初始设置

### 方案一：Fork现有仓库（推荐）
如果您没有原仓库的推送权限：

```bash
# 1. 在GitHub上fork原仓库到您的账户
# 2. 克隆您的fork版本
git clone https://github.com/YOUR_USERNAME/hand-tracking-using-mediapipe.git
cd hand-tracking-using-mediapipe

# 3. 添加原仓库作为upstream
git remote add upstream https://github.com/Sousannah/hand-tracking-using-mediapipe.git

# 4. 验证远程仓库配置
git remote -v
```

### 方案二：创建自己的仓库
```bash
# 1. 在GitHub创建新仓库
# 2. 更改远程仓库地址
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 3. 推送所有内容
git push -u origin main
```

---

## 🔑 权限配置

### GitHub Token认证（推荐）
```bash
# 1. 生成Personal Access Token
# GitHub → Settings → Developer settings → Personal access tokens → Generate new token

# 2. 配置Git使用token
git config --global credential.helper store

# 3. 第一次推送时输入用户名和token（而不是密码）
git push origin main
# Username: YOUR_USERNAME  
# Password: YOUR_TOKEN
```

### SSH密钥认证
```bash
# 1. 生成SSH密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 添加到ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 3. 复制公钥到GitHub
cat ~/.ssh/id_ed25519.pub
# 在GitHub Settings → SSH and GPG keys 中添加

# 4. 更改仓库URL为SSH格式
git remote set-url origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
```

---

## 🔄 日常工作流程

### 开始工作前（每次都要做）
```bash
# 1. 检查当前状态
git status

# 2. 拉取最新更改
git pull origin main

# 如果有upstream（fork仓库）
git fetch upstream
git merge upstream/main

# 3. 创建功能分支（可选但推荐）
git checkout -b feature/hand-gesture-improvements
```

### 完成工作后
```bash
# 1. 查看修改
git status
git diff

# 2. 添加修改
git add .
# 或者选择性添加
git add specific_file.py

# 3. 提交修改
git commit -m "feat: 添加新的手势识别功能"

# 4. 推送到远程
git push origin main
# 或推送功能分支
git push origin feature/hand-gesture-improvements
```

### 在另一台电脑上
```bash
# 1. 克隆仓库（首次）
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# 2. 同步最新更改（日常）
git pull origin main

# 3. 如果本地有未提交的更改
git stash                    # 暂存当前更改
git pull origin main         # 拉取最新
git stash pop               # 恢复暂存的更改
```

---

## ⚡ 冲突解决

### 合并冲突
```bash
# 1. 拉取时出现冲突
git pull origin main
# Auto-merging file.py
# CONFLICT (content): Merge conflict in file.py

# 2. 查看冲突文件
git status

# 3. 手动编辑冲突文件，查找并解决：
# <<<<<<< HEAD
# 您的代码
# =======
# 远程代码
# >>>>>>> commit_id

# 4. 标记冲突已解决
git add conflicted_file.py

# 5. 完成合并
git commit -m "解决合并冲突"

# 6. 推送
git push origin main
```

### 避免冲突的策略
```bash
# 1. 使用功能分支
git checkout -b feature/new-feature
# 在分支上工作
git checkout main
git pull origin main
git merge feature/new-feature

# 2. 频繁同步
# 每天开始工作前和结束后都同步

# 3. 小而频繁的提交
# 避免大量更改堆积
```

---

## 🎯 最佳实践

### 提交信息规范
```bash
# 格式：type(scope): description
git commit -m "feat(gesture): 添加手势识别算法"
git commit -m "fix(camera): 修复摄像头连接问题"  
git commit -m "docs(readme): 更新安装说明"
git commit -m "refactor(ui): 重构界面代码"
```

### 分支策略
```bash
# 主分支：main（生产代码）
# 开发分支：develop（开发代码）
# 功能分支：feature/feature-name
# 修复分支：fix/bug-name

# 创建功能分支
git checkout -b feature/ue5-integration

# 合并回主分支
git checkout main
git merge feature/ue5-integration
git branch -d feature/ue5-integration
```

### 定期维护
```bash
# 每周执行一次
git fetch --prune              # 清理远程分支引用
git branch -d merged_branch    # 删除已合并分支
git gc                         # 垃圾回收
```

---

## 🆘 紧急恢复

### 撤销最后一次提交
```bash
# 保留更改，撤销提交
git reset --soft HEAD~1

# 完全撤销（危险操作）
git reset --hard HEAD~1
```

### 恢复删除的文件
```bash
# 恢复未提交的删除
git checkout -- deleted_file.py

# 从特定提交恢复
git checkout commit_id -- deleted_file.py
```

### 强制同步（谨慎使用）
```bash
# 将本地强制同步到远程状态
git fetch origin
git reset --hard origin/main
```

---

## 📱 多设备同步检查清单

### 每次开始工作前
- [ ] `git status` 检查状态
- [ ] `git pull origin main` 拉取最新
- [ ] 解决任何冲突
- [ ] 开始编码

### 每次结束工作后  
- [ ] `git add .` 添加更改
- [ ] `git commit -m "描述"` 提交
- [ ] `git push origin main` 推送
- [ ] 验证推送成功

### 切换设备时
- [ ] 确保上一台设备已推送
- [ ] 新设备上拉取最新
- [ ] 验证代码是最新的

---

## 🛠️ 实用命令速查

```bash
# 查看状态
git status
git log --oneline -10

# 同步操作
git pull origin main
git push origin main

# 分支操作
git branch                     # 查看分支
git checkout -b new-branch     # 创建并切换分支
git merge branch-name          # 合并分支

# 暂存操作
git stash                      # 暂存更改
git stash pop                  # 恢复暂存
git stash list                 # 查看暂存列表

# 查看差异
git diff                       # 查看未暂存的更改
git diff --staged              # 查看已暂存的更改
git diff HEAD~1                # 与上一次提交比较
```

---

## 📞 问题排查

### 推送失败
```bash
# 403错误：权限问题
# 检查认证配置，使用token或SSH

# 422错误：分支保护
# 使用Pull Request流程

# 冲突错误：先拉取后推送
git pull origin main
# 解决冲突后再推送
```

### 同步失败
```bash
# 网络问题
git config --global http.proxy http://proxy:port

# 仓库损坏
git fsck
git gc --aggressive
```

**记住：频繁同步，小步提交，及时沟通！** 🚀 