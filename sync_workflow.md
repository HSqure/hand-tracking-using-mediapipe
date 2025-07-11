# 多设备Git同步工作流程指南

## 🔄 每次开始工作前（必做！）

### 步骤1：检查当前状态
```bash
git status
```

### 步骤2：拉取最新代码
```bash
git pull origin main
```

### 步骤3：如果有冲突，先解决冲突再继续工作

---

## 💾 每次结束工作后（必做！）

### 步骤1：检查修改
```bash
git status
git diff
```

### 步骤2：添加修改
```bash
git add .
```

### 步骤3：提交修改
```bash
git commit -m "描述您的修改内容"
```

### 步骤4：推送到远程仓库
```bash
git push origin main
```

---

## ⚠️ 冲突处理方案

### 当git pull出现冲突时：

1. **查看冲突文件：**
```bash
git status
```

2. **手动编辑冲突文件，移除冲突标记：**
```
<<<<<<< HEAD
你的修改
=======
远程的修改
>>>>>>> branch_name
```

3. **解决冲突后：**
```bash
git add .
git commit -m "解决合并冲突"
git push origin main
```

---

## 🚨 紧急情况处理

### 如果推送失败（有人先推送了）：
```bash
git pull origin main
# 解决可能的冲突
git push origin main
```

### 如果本地有未提交的修改，但需要拉取：
```bash
git stash                    # 暂存当前修改
git pull origin main         # 拉取最新代码
git stash pop               # 恢复暂存的修改
```

---

## 📝 最佳实践

1. **频繁提交：** 每个小功能完成就提交
2. **描述清晰：** commit message要写清楚改了什么
3. **及时推送：** 每天工作结束前必须推送
4. **拉取优先：** 每天开始工作前必须拉取
5. **分支管理：** 大功能开发建议用分支

---

## 🛡️ 避免数据丢失的保险措施

### 重要修改前备份：
```bash
git branch backup-$(date +%Y%m%d)
```

### 查看提交历史：
```bash
git log --oneline -10
```

### 恢复到之前的版本：
```bash
git reset --hard 提交哈希值
``` 