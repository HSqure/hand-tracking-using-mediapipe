# 多设备同步使用指南

## 🚀 快速使用

### 每天开始工作时：
```powershell
.\start_work.ps1
```

### 每天结束工作时：
```powershell
.\end_work.ps1 "今天完成了什么功能"
```

## 📁 文件说明

- `sync_workflow.md` - 详细的同步工作流程指南
- `start_work.ps1` - 开始工作前自动同步脚本
- `end_work.ps1` - 结束工作后自动提交推送脚本
- `README_sync.md` - 本使用说明

## 💡 使用示例

### 电脑A上的工作流程：
```powershell
# 早上开始工作
.\start_work.ps1

# 修改代码...
# 完成一个功能后
.\end_work.ps1 "添加了新的手势识别功能"

# 或者多次提交
.\end_work.ps1 "修复了大拇指检测bug"
.\end_work.ps1 "优化了fps显示"
```

### 电脑B上的工作流程：
```powershell
# 在另一台电脑上开始工作
.\start_work.ps1  # 自动拉取电脑A的修改

# 继续开发...
.\end_work.ps1 "增加了3D坐标显示"
```

## ⚠️ 注意事项

1. **脚本执行权限**: 首次使用可能需要设置PowerShell执行策略：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **提交信息**: 务必写清楚每次修改的内容，方便追踪

3. **冲突处理**: 如果出现冲突，脚本会提示，请手动解决后重新运行

## 🔧 高级使用

### 查看最近的提交：
```bash
git log --oneline -5
```

### 创建功能分支：
```bash
git checkout -b feature-new-gestures
# 开发完成后
git checkout main
git merge feature-new-gestures
git push origin main
```

### 暂存修改（临时切换工作）：
```bash
git stash
git pull origin main
git stash pop
``` 