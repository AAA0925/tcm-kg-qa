# 中医知识图谱构建快速启动脚本
# 使用示例：.\setup_kg.ps1 -Password "your_password"

param(
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [string]$Website = "http://localhost:7474",
    [string]$User = "neo4j",
    [string]$DBName = "neo4j",
    [string]$DataPath = "data/medical_new_2.json",
    [string]$ExportDir = "data"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  中医知识图谱构建工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查数据文件是否存在
if (-Not (Test-Path $DataPath)) {
    Write-Host "❌ 错误：数据文件不存在 - $DataPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 数据文件检查通过：$DataPath" -ForegroundColor Green
Write-Host ""

# 显示配置信息
Write-Host "配置信息:" -ForegroundColor Yellow
Write-Host "  Neo4j 地址：$Website"
Write-Host "  用户名：$User"
Write-Host "  数据库：$DBName"
Write-Host "  数据文件：$DataPath"
Write-Host "  导出目录：$ExportDir"
Write-Host ""

# 询问是否继续
$continue = Read-Host "是否继续构建知识图谱？(y/n)"
if ($continue -ne 'y') {
    Write-Host "❌ 已取消操作" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🚀 开始构建知识图谱..." -ForegroundColor Green
Write-Host ""

# 执行构建脚本
try {
    python build_up_graph.py `
        --website $Website `
        --user $User `
        --password $Password `
        --dbname $DBName `
        --data $DataPath `
        --export-dir $ExportDir
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ 知识图谱构建成功!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "下一步操作:" -ForegroundColor Yellow
        Write-Host "  1. 访问 Neo4j Browser: $Website"
        Write-Host "  2. 运行查询验证数据："
        Write-Host "     MATCH (n) RETURN labels(n)[0] as type, count(*) as count GROUP BY type"
        Write-Host "  3. 启动后端服务测试 API"
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "❌ 构建过程中出现错误，请检查日志" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ 发生异常：$_" -ForegroundColor Red
    exit 1
}
