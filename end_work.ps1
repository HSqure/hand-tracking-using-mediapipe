# 结束工作后的自动提交推送脚本
# 使用方法: .\end_work.ps1 "提交信息"

param(
    [Parameter(Mandatory=$true)]
    [string]$CommitMessage
)

Write-Host "=== 结束工作后同步提交 ===" -ForegroundColor Green
Write-Host ""

# 检查修改状态
Write-Host "📋 检查当前修改..." -ForegroundColor Yellow
git status

Write-Host ""
$hasChanges = git diff --name-only
if (-not $hasChanges) {
    $hasChanges = git diff --staged --name-only
}

if (-not $hasChanges) {
    Write-Host "ℹ️  没有发现修改，无需提交" -ForegroundColor Blue
    exit 0
}

Write-Host "📝 发现以下修改:" -ForegroundColor Cyan
git diff --name-only
git diff --staged --name-only

Write-Host ""
Write-Host "➕ 添加所有修改到暂存区..." -ForegroundColor Yellow
git add .

Write-Host ""
Write-Host "💾 提交修改..." -ForegroundColor Yellow
try {
    git commit -m $CommitMessage
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 提交成功！" -ForegroundColor Green
    } else {
        Write-Host "❌ 提交失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 提交过程出错" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 推送到远程仓库..." -ForegroundColor Yellow

# 先尝试推送，如果失败则先拉取再推送
try {
    git push origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 推送成功！代码已同步到GitHub！" -ForegroundColor Green
    } else {
        Write-Host "⚠️  推送失败，可能有人先推送了代码" -ForegroundColor Yellow
        Write-Host "正在拉取最新代码并重新推送..." -ForegroundColor Yellow
        
        git pull origin main
        if ($LASTEXITCODE -eq 0) {
            git push origin main
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ 同步后推送成功！" -ForegroundColor Green
            } else {
                Write-Host "❌ 推送仍然失败，请手动检查" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ 拉取失败，可能有冲突需要手动解决" -ForegroundColor Red
            Write-Host "请参考 sync_workflow.md 解决冲突" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "❌ 推送过程出错，请检查网络连接" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 当前状态:" -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "=== 工作结束同步完成 ===" -ForegroundColor Green 