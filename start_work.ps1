# 开始工作前的自动同步脚本
# 使用方法: .\start_work.ps1

Write-Host "=== 开始工作前同步检查 ===" -ForegroundColor Green
Write-Host ""

# 检查当前状态
Write-Host "📋 检查当前Git状态..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "🔄 拉取最新代码..." -ForegroundColor Yellow

# 拉取最新代码
try {
    git pull origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 同步成功！可以开始工作了！" -ForegroundColor Green
    } else {
        Write-Host "⚠️  拉取过程中可能有冲突，请检查并手动解决" -ForegroundColor Red
        Write-Host "冲突解决方法请参考 sync_workflow.md" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ 拉取失败，请检查网络连接" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 当前分支状态:" -ForegroundColor Cyan
git branch -v

Write-Host ""
Write-Host "=== 同步检查完成 ===" -ForegroundColor Green 