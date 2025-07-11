# 🚀 终极智能Git同步脚本 (PowerShell版)
# 作者: 为大哥量身定制的最先进同步解决方案
# 版本: 2.0 Ultimate Edition

param(
    [Parameter(Position=0)]
    [string]$Action = "",
    
    [Parameter(Position=1)]
    [string]$CommitMessage = "",
    
    [switch]$Force,
    [switch]$Verbose,
    [switch]$DryRun,
    [switch]$AutoResolve
)

# 设置控制台编码支持中文
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 全局配置
$Config = @{
    MaxRetries = 3
    BackupEnabled = $true
    LogLevel = if ($Verbose) { "Verbose" } else { "Info" }
    Colors = @{
        Success = "Green"
        Warning = "Yellow"
        Error = "Red"
        Info = "Cyan"
        Header = "Magenta"
    }
}

# 日志记录类
class GitSyncLogger {
    [string]$LogFile
    [string]$LogLevel
    
    GitSyncLogger([string]$level) {
        $this.LogLevel = $level
        $this.LogFile = "git_sync_$(Get-Date -Format 'yyyyMMdd').log"
    }
    
    [void]LogMessage([string]$level, [string]$message) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] [$level] $message"
        Add-Content -Path $this.LogFile -Value $logEntry -Encoding UTF8
        
        if ($this.LogLevel -eq "Verbose" -or $level -ne "DEBUG") {
            $color = switch ($level) {
                "SUCCESS" { "Green" }
                "WARNING" { "Yellow" }
                "ERROR" { "Red" }
                "INFO" { "Cyan" }
                default { "White" }
            }
            Write-Host $message -ForegroundColor $color
        }
    }
    
    [void]Success([string]$message) { $this.LogMessage("SUCCESS", "✅ $message") }
    [void]Warning([string]$message) { $this.LogMessage("WARNING", "⚠️ $message") }
    [void]Error([string]$message) { $this.LogMessage("ERROR", "❌ $message") }
    [void]Info([string]$message) { $this.LogMessage("INFO", "📋 $message") }
    [void]Header([string]$message) { 
        Write-Host "`n$('=' * 50)" -ForegroundColor Magenta
        Write-Host $message -ForegroundColor Magenta
        Write-Host "$('=' * 50)" -ForegroundColor Magenta
        $this.LogMessage("HEADER", $message)
    }
}

# Git状态分析类
class GitStatusAnalyzer {
    [object]$Status
    [array]$UntrackedFiles
    [array]$ModifiedFiles
    [array]$StagedFiles
    [array]$ConflictFiles
    
    GitStatusAnalyzer() {
        $this.AnalyzeStatus()
    }
    
    [void]AnalyzeStatus() {
        try {
            $gitStatus = git status --porcelain 2>$null
            if ($LASTEXITCODE -ne 0) {
                throw "不是Git仓库或Git命令失败"
            }
            
            $this.UntrackedFiles = @()
            $this.ModifiedFiles = @()
            $this.StagedFiles = @()
            $this.ConflictFiles = @()
            
            foreach ($line in $gitStatus) {
                $status = $line.Substring(0, 2)
                $file = $line.Substring(3)
                
                switch -Regex ($status) {
                    "^\?\?" { $this.UntrackedFiles += $file }
                    "^.M" { $this.ModifiedFiles += $file }
                    "^M." { $this.StagedFiles += $file }
                    "^UU" { $this.ConflictFiles += $file }
                    "^AA" { $this.ConflictFiles += $file }
                }
            }
        }
        catch {
            throw "Git状态分析失败: $_"
        }
    }
    
    [bool]HasChanges() {
        return ($this.UntrackedFiles.Count + $this.ModifiedFiles.Count + $this.StagedFiles.Count) -gt 0
    }
    
    [bool]HasConflicts() {
        return $this.ConflictFiles.Count -gt 0
    }
    
    [hashtable]GetSummary() {
        return @{
            Untracked = $this.UntrackedFiles.Count
            Modified = $this.ModifiedFiles.Count
            Staged = $this.StagedFiles.Count
            Conflicts = $this.ConflictFiles.Count
            Total = $this.UntrackedFiles.Count + $this.ModifiedFiles.Count + $this.StagedFiles.Count
        }
    }
}

# 主同步管理器类
class GitSyncManager {
    [GitSyncLogger]$Logger
    [GitStatusAnalyzer]$StatusAnalyzer
    [bool]$DryRun
    [bool]$AutoResolve
    
    GitSyncManager([bool]$dryRun, [bool]$autoResolve, [string]$logLevel) {
        $this.Logger = [GitSyncLogger]::new($logLevel)
        $this.DryRun = $dryRun
        $this.AutoResolve = $autoResolve
        $this.StatusAnalyzer = [GitStatusAnalyzer]::new()
    }
    
    [void]ShowWelcome() {
        $this.Logger.Header("🚀 终极智能Git同步系统 v2.0")
        $this.Logger.Info("欢迎使用最先进的PowerShell Git同步解决方案！")
        $this.Logger.Info("仓库: $(Split-Path -Leaf (Get-Location))")
        $this.Logger.Info("时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
        if ($this.DryRun) {
            $this.Logger.Warning("🧪 演练模式 - 不会执行实际的Git操作")
        }
    }
    
    [void]CheckGitRepository() {
        $this.Logger.Info("🔍 验证Git仓库...")
        
        if (-not (Test-Path ".git")) {
            $this.Logger.Error("当前目录不是Git仓库")
            throw "请在Git仓库根目录运行此脚本"
        }
        
        # 检查远程仓库连接
        try {
            $remote = git remote get-url origin 2>$null
            if ($LASTEXITCODE -eq 0) {
                $this.Logger.Success("Git仓库验证通过: $remote")
            } else {
                $this.Logger.Warning("未找到origin远程仓库")
            }
        }
        catch {
            $this.Logger.Warning("远程仓库连接检查失败")
        }
    }
    
    [void]ShowDetailedStatus() {
        $this.Logger.Header("📊 详细状态分析")
        
        $summary = $this.StatusAnalyzer.GetSummary()
        
        $this.Logger.Info("📈 文件统计:")
        Write-Host "  🆕 未跟踪文件: $($summary.Untracked)" -ForegroundColor Yellow
        Write-Host "  📝 已修改文件: $($summary.Modified)" -ForegroundColor Blue
        Write-Host "  ✅ 已暂存文件: $($summary.Staged)" -ForegroundColor Green
        Write-Host "  ⚠️ 冲突文件: $($summary.Conflicts)" -ForegroundColor Red
        
        if ($this.StatusAnalyzer.UntrackedFiles.Count -gt 0) {
            $this.Logger.Warning("🆕 发现新文件:")
            foreach ($file in $this.StatusAnalyzer.UntrackedFiles) {
                Write-Host "    📄 $file" -ForegroundColor Yellow
            }
        }
        
        if ($this.StatusAnalyzer.ModifiedFiles.Count -gt 0) {
            $this.Logger.Info("📝 已修改文件:")
            foreach ($file in $this.StatusAnalyzer.ModifiedFiles) {
                Write-Host "    📄 $file" -ForegroundColor Blue
            }
        }
        
        if ($this.StatusAnalyzer.HasConflicts()) {
            $this.Logger.Error("⚠️ 发现冲突文件:")
            foreach ($file in $this.StatusAnalyzer.ConflictFiles) {
                Write-Host "    ⚠️ $file" -ForegroundColor Red
            }
        }
    }
    
    [bool]HandleNewFiles() {
        if ($this.StatusAnalyzer.UntrackedFiles.Count -eq 0) {
            $this.Logger.Success("没有发现新文件")
            return $true
        }
        
        $this.Logger.Warning("🆕 发现 $($this.StatusAnalyzer.UntrackedFiles.Count) 个新文件")
        
        if (-not $this.AutoResolve) {
            $response = Read-Host "是否添加所有新文件到Git跟踪? [Y/N/S=选择性添加]"
            switch ($response.ToUpper()) {
                "Y" { 
                    $this.Logger.Info("✅ 用户选择添加所有新文件")
                }
                "S" {
                    return $this.SelectiveAddFiles()
                }
                default { 
                    $this.Logger.Warning("❌ 用户选择不添加新文件，退出同步")
                    return $false 
                }
            }
        }
        
        return $this.AddAllFiles()
    }
    
    [bool]SelectiveAddFiles() {
        $this.Logger.Info("🎯 选择性添加文件模式")
        $filesToAdd = @()
        
        foreach ($file in $this.StatusAnalyzer.UntrackedFiles) {
            $response = Read-Host "添加文件 '$file'? [Y/N]"
            if ($response.ToUpper() -eq "Y") {
                $filesToAdd += $file
            }
        }
        
        if ($filesToAdd.Count -eq 0) {
            $this.Logger.Warning("未选择任何文件添加")
            return $false
        }
        
        foreach ($file in $filesToAdd) {
            if (-not $this.DryRun) {
                git add $file
                if ($LASTEXITCODE -eq 0) {
                    $this.Logger.Success("✅ 已添加: $file")
                } else {
                    $this.Logger.Error("❌ 添加失败: $file")
                    return $false
                }
            } else {
                $this.Logger.Info("🧪 [演练] 将添加: $file")
            }
        }
        
        return $true
    }
    
    [bool]AddAllFiles() {
        $this.Logger.Info("➕ 添加所有修改和新文件...")
        
        if (-not $this.DryRun) {
            git add .
            if ($LASTEXITCODE -eq 0) {
                $this.Logger.Success("✅ 所有文件已添加到暂存区")
                return $true
            } else {
                $this.Logger.Error("❌ 添加文件失败")
                return $false
            }
        } else {
            $this.Logger.Info("🧪 [演练] 将执行: git add .")
            return $true
        }
    }
    
    [bool]CommitChanges([string]$message) {
        if ([string]::IsNullOrEmpty($message)) {
            $message = Read-Host "请输入提交信息"
        }
        
        $this.Logger.Info("💾 提交修改: '$message'")
        
        if (-not $this.DryRun) {
            git commit -m $message
            if ($LASTEXITCODE -eq 0) {
                $this.Logger.Success("✅ 提交成功!")
                return $true
            } else {
                $this.Logger.Error("❌ 提交失败")
                return $false
            }
        } else {
            $this.Logger.Info("🧪 [演练] 将执行: git commit -m '$message'")
            return $true
        }
    }
    
    [bool]PushChanges() {
        $this.Logger.Info("🚀 推送到远程仓库...")
        
        for ($i = 1; $i -le $Config.MaxRetries; $i++) {
            if (-not $this.DryRun) {
                git push origin main
                if ($LASTEXITCODE -eq 0) {
                    $this.Logger.Success("✅ 推送成功!")
                    return $true
                } else {
                    $this.Logger.Warning("⚠️ 推送失败 (尝试 $i/$($Config.MaxRetries))")
                    if ($i -lt $Config.MaxRetries) {
                        $this.Logger.Info("🔄 尝试先拉取远程更新...")
                        if ($this.PullChanges()) {
                            continue
                        }
                    }
                }
            } else {
                $this.Logger.Info("🧪 [演练] 将执行: git push origin main")
                return $true
            }
        }
        
        $this.Logger.Error("❌ 推送失败，已达最大重试次数")
        return $false
    }
    
    [bool]PullChanges() {
        $this.Logger.Info("🔄 拉取远程更新...")
        
        if (-not $this.DryRun) {
            git pull origin main
            if ($LASTEXITCODE -eq 0) {
                $this.Logger.Success("✅ 拉取成功!")
                # 重新分析状态
                $this.StatusAnalyzer = [GitStatusAnalyzer]::new()
                return $true
            } else {
                $this.Logger.Error("❌ 拉取失败，可能存在冲突")
                return $false
            }
        } else {
            $this.Logger.Info("🧪 [演练] 将执行: git pull origin main")
            return $true
        }
    }
    
    [void]ShowFinalStatus() {
        $this.Logger.Header("📊 最终状态报告")
        
        # 显示最近的提交
        $this.Logger.Info("📈 最近3次提交:")
        if (-not $this.DryRun) {
            $commits = git log --oneline -3 2>$null
            if ($LASTEXITCODE -eq 0) {
                foreach ($commit in $commits) {
                    Write-Host "  🔹 $commit" -ForegroundColor Green
                }
            }
        }
        
        # 显示当前状态
        $this.Logger.Info("📋 当前工作目录状态:")
        if (-not $this.DryRun) {
            $status = git status --short 2>$null
            if ($status) {
                foreach ($line in $status) {
                    Write-Host "  $line" -ForegroundColor Yellow
                }
            } else {
                $this.Logger.Success("🎉 工作目录干净，所有修改已同步!")
            }
        }
        
        $this.Logger.Success("🚀 同步操作完成!")
    }
}

# 主函数
function Main {
    try {
        $syncManager = [GitSyncManager]::new($DryRun, $AutoResolve, $Config.LogLevel)
        $syncManager.ShowWelcome()
        
        # 检查Git仓库
        $syncManager.CheckGitRepository()
        
        switch ($Action.ToLower()) {
            "pull" {
                $syncManager.PullChanges()
                $syncManager.ShowFinalStatus()
                return
            }
            "check" {
                $syncManager.ShowDetailedStatus()
                return
            }
            "status" {
                $syncManager.ShowDetailedStatus()
                return
            }
            "" {
                if ([string]::IsNullOrEmpty($CommitMessage)) {
                    Write-Host "🚀 终极智能Git同步系统 v2.0" -ForegroundColor Magenta
                    Write-Host ""
                    Write-Host "使用方法:" -ForegroundColor Cyan
                    Write-Host "  .\smart_sync_ultimate.ps1 '提交信息'       - 完整同步"
                    Write-Host "  .\smart_sync_ultimate.ps1 pull            - 仅拉取"
                    Write-Host "  .\smart_sync_ultimate.ps1 check           - 检查状态"
                    Write-Host "  .\smart_sync_ultimate.ps1 status          - 详细状态"
                    Write-Host ""
                    Write-Host "高级选项:" -ForegroundColor Yellow
                    Write-Host "  -DryRun         演练模式，不执行实际操作"
                    Write-Host "  -Verbose        详细日志输出"
                    Write-Host "  -AutoResolve    自动处理新文件"
                    Write-Host "  -Force          强制执行"
                    Write-Host ""
                    Write-Host "示例:" -ForegroundColor Green
                    Write-Host "  .\smart_sync_ultimate.ps1 '添加新功能' -Verbose"
                    Write-Host "  .\smart_sync_ultimate.ps1 pull -DryRun"
                    return
                }
                $Action = $CommitMessage
                $CommitMessage = ""
            }
        }
        
        # 完整同步流程
        $syncManager.ShowDetailedStatus()
        
        # 处理冲突
        if ($syncManager.StatusAnalyzer.HasConflicts()) {
            $syncManager.Logger.Error("⚠️ 检测到合并冲突，请手动解决后重新运行")
            return
        }
        
        # 检查是否有修改需要同步
        if (-not $syncManager.StatusAnalyzer.HasChanges()) {
            $syncManager.Logger.Info("📭 没有需要同步的修改")
            $syncManager.PullChanges()
            $syncManager.ShowFinalStatus()
            return
        }
        
        # 处理新文件
        if (-not $syncManager.HandleNewFiles()) {
            return
        }
        
        # 提交修改
        if (-not $syncManager.CommitChanges($Action)) {
            return
        }
        
        # 推送修改
        if (-not $syncManager.PushChanges()) {
            return
        }
        
        # 显示最终状态
        $syncManager.ShowFinalStatus()
        
    }
    catch {
        Write-Host "❌ 发生严重错误: $_" -ForegroundColor Red
        Write-Host "💡 请检查网络连接和Git配置" -ForegroundColor Yellow
        exit 1
    }
}

# 执行主函数
Main 