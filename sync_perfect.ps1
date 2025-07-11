# 🚀 完美Git同步脚本 (PowerShell终极版)
# 最先进的多设备同步解决方案
# 版本: 3.0 Perfect Edition

param(
    [Parameter(Position=0)]
    [string]$Message = "",
    
    [switch]$Pull,
    [switch]$Check,
    [switch]$DryRun,
    [switch]$Auto
)

# 颜色输出函数
function Write-ColorText {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

function Write-Header {
    param([string]$Text)
    Write-Host "`n$('=' * 60)" -ForegroundColor Magenta
    Write-Host $Text -ForegroundColor Magenta
    Write-Host "$('=' * 60)" -ForegroundColor Magenta
}

# 显示帮助信息
if ([string]::IsNullOrEmpty($Message) -and -not $Pull -and -not $Check) {
    Write-ColorText "🚀 完美Git同步系统 v3.0" "Magenta"
    Write-ColorText ""
    Write-ColorText "使用方法:" "Cyan"
    Write-ColorText "  .\sync_perfect.ps1 '提交信息'     - 完整同步" "White"
    Write-ColorText "  .\sync_perfect.ps1 -Pull         - 仅拉取" "White"
    Write-ColorText "  .\sync_perfect.ps1 -Check        - 检查状态" "White"
    Write-ColorText ""
    Write-ColorText "高级选项:" "Yellow"
    Write-ColorText "  -DryRun      演练模式，不执行实际操作" "White"
    Write-ColorText "  -Auto        自动处理新文件" "White"
    Write-ColorText ""
    Write-ColorText "示例:" "Green"
    Write-ColorText "  .\sync_perfect.ps1 '添加新功能' -Auto" "White"
    Write-ColorText "  .\sync_perfect.ps1 -Pull -DryRun" "White"
    exit 0
}

Write-Header "🚀 完美Git同步系统 v3.0"
Write-ColorText "📋 PowerShell最先进同步解决方案" "Cyan"
Write-ColorText "📁 仓库: $(Split-Path -Leaf (Get-Location))" "Cyan"
Write-ColorText "🕒 时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Cyan"

if ($DryRun) {
    Write-ColorText "🧪 演练模式 - 不会执行实际的Git操作" "Yellow"
}

# 验证Git仓库
if (-not (Test-Path ".git")) {
    Write-ColorText "❌ 当前目录不是Git仓库" "Red"
    exit 1
}

# 检查远程仓库
$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-ColorText "✅ Git仓库验证通过: $remote" "Green"
}

# 处理拉取模式
if ($Pull) {
    Write-ColorText "🔄 拉取远程更新..." "Cyan"
    if (-not $DryRun) {
        git pull origin main
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✅ 拉取成功!" "Green"
        } else {
            Write-ColorText "❌ 拉取失败" "Red"
        }
    } else {
        Write-ColorText "🧪 [演练模式] 将执行: git pull origin main" "Cyan"
    }
    exit 0
}

# 处理检查模式
if ($Check) {
    Write-ColorText "📊 检查Git状态..." "Cyan"
    git status
    Write-ColorText "📈 最近3次提交:" "Cyan"
    git log --oneline -3
    exit 0
}

# 完整同步流程
Write-ColorText "📋 检查当前Git状态..." "Cyan"
$gitStatus = git status --porcelain

if ($gitStatus) {
    Write-ColorText "🆕 发现需要同步的文件:" "Yellow"
    foreach ($line in $gitStatus) {
        Write-ColorText "    📄 $line" "Yellow"
    }
    
    if (-not $Auto) {
        $response = Read-Host "是否添加所有文件并提交? [Y/N]"
        if ($response.ToUpper() -ne "Y") {
            Write-ColorText "❌ 用户取消同步" "Red"
            exit 0
        }
    }
    
    Write-ColorText "➕ 添加所有文件..." "Cyan"
    if (-not $DryRun) {
        git add .
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✅ 文件添加成功" "Green"
        } else {
            Write-ColorText "❌ 文件添加失败" "Red"
            exit 1
        }
    } else {
        Write-ColorText "🧪 [演练模式] 将执行: git add ." "Cyan"
    }
    
    Write-ColorText "💾 提交修改: '$Message'" "Cyan"
    if (-not $DryRun) {
        git commit -m $Message
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✅ 提交成功!" "Green"
        } else {
            Write-ColorText "❌ 提交失败" "Red"
            exit 1
        }
    } else {
        Write-ColorText "🧪 [演练模式] 将执行: git commit -m '$Message'" "Cyan"
    }
    
    Write-ColorText "🚀 推送到远程仓库..." "Cyan"
    if (-not $DryRun) {
        git push origin main
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✅ 推送成功!" "Green"
        } else {
            Write-ColorText "❌ 推送失败" "Red"
            exit 1
        }
    } else {
        Write-ColorText "🧪 [演练模式] 将执行: git push origin main" "Cyan"
    }
    
    Write-ColorText "🎉 同步完成!" "Green"
} else {
    Write-ColorText "📭 没有需要同步的修改" "Cyan"
    Write-ColorText "🔄 检查远程更新..." "Cyan"
    
    if (-not $DryRun) {
        git pull origin main
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✅ 已是最新版本!" "Green"
        }
    } else {
        Write-ColorText "🧪 [演练模式] 将检查远程更新" "Cyan"
    }
}

Write-Header "📊 最终状态"
Write-ColorText "📈 最近3次提交:" "Cyan"
if (-not $DryRun) {
    git log --oneline -3
}
Write-ColorText "🚀 操作完成!" "Green"
