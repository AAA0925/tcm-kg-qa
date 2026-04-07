"""
API 文档自动生成器
扫描所有 API 路由并生成 Markdown 文档
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class APIDocGenerator:
    """API 文档生成器"""
    
    def __init__(self, api_dir: str = "backend/app/api"):
        self.api_dir = Path(api_dir)
        self.routes = {}
        
    def scan_api_files(self):
        """扫描所有 API 文件"""
        print(f"📂 正在扫描 API 目录：{self.api_dir}")
        
        for file_path in self.api_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            
            print(f"  📄 分析文件：{file_path.name}")
            routes = self.parse_api_file(file_path)
            
            # 根据文件名确定模块名
            module_name = file_path.stem
            if routes:
                self.routes[module_name] = routes
        
        print(f"✅ 共发现 {len(self.routes)} 个 API 模块\n")
    
    def parse_api_file(self, file_path: Path) -> Dict:
        """解析单个 API 文件，提取路由信息"""
        routes = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配路由装饰器
        route_pattern = r'@router\.(get|post|put|delete)\(["\'](/[^"\']+)["\']\)'
        func_pattern = r'async def (\w+)\([^)]*\):'
        docstring_pattern = r'"""([^"]+)"""'
        
        matches = re.finditer(route_pattern, content)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            
            # 查找对应的函数名和文档字符串
            start_pos = match.end()
            remaining_content = content[start_pos:start_pos + 500]
            
            func_match = re.search(func_pattern, remaining_content)
            if func_match:
                func_name = func_match.group(1)
                
                # 查找文档字符串
                doc_match = re.search(docstring_pattern, remaining_content)
                description = doc_match.group(1).strip() if doc_match else ""
                
                routes[path] = {
                    'method': method,
                    'function': func_name,
                    'description': description,
                    'path': path
                }
        
        return routes
    
    def generate_markdown(self) -> str:
        """生成 Markdown 文档"""
        md = []
        
        # 标题
        md.append("# 中医知识图谱问答系统 - API 接口文档\n")
        md.append(f"> **版本**: v1.0.0  ")
        md.append(f"> **最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        md.append("> **基础地址**: http://localhost:8000/api\n")
        md.append("---\n")
        
        # 目录
        md.append("## 📋 目录\n")
        for module_name in sorted(self.routes.keys()):
            module_title = self._get_module_title(module_name)
            anchor = self._get_anchor(module_title)
            md.append(f"- [{module_title}](#{anchor})")
        md.append("")
        
        # 各模块接口详情
        for module_name in sorted(self.routes.keys()):
            module_title = self._get_module_title(module_name)
            routes = self.routes[module_name]
            
            md.append(f"---\n")
            md.append(f"## {self._get_module_emoji(module_name)} {module_title}\n")
            
            if module_name == 'admin':
                md.append("\n> ⚠️ **仅管理员角色可访问**\n")
            
            md.append("")
            
            # 按路径排序
            for path in sorted(routes.keys()):
                route = routes[path]
                md.append(f"### {route['method']} `{path}`\n")
                
                if route['description']:
                    md.append(f"{route['description']}\n")
                
                # 添加参数说明区域
                md.append("**请求参数**:\n")
                md.append("```json\n// TODO: 补充参数示例\n```\n")
                
                md.append("**响应示例**:\n")
                md.append("```json\n// TODO: 补充响应示例\n```\n")
                
                md.append("")
        
        # 错误响应格式
        md.append("---\n")
        md.append("## 📝 错误响应格式\n")
        md.append("""所有接口在发生错误时统一返回以下格式：

```json
{
  "detail": "错误描述信息"
}
```

常见 HTTP 状态码说明：
- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问（缺少或无效的 token）
- `403 Forbidden`: 禁止访问（权限不足）
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误
""")
        
        # 认证说明
        md.append("---\n")
        md.append("## 🔑 认证说明\n")
        md.append("""需要认证的接口需要在请求头中包含 `Authorization` 字段：

```
Authorization: Bearer <your_access_token>
```

Token 通过 `/api/auth/login` 接口登录后获得。
""")
        
        # 实体类型说明
        md.append("---\n")
        md.append("## 📊 实体类型说明\n")
        md.append("""系统支持的实体类型：
- `Disease`: 疾病
- `Drug`: 药品
- `Food`: 食物
- `Check`: 检查
- `Department`: 科室
- `Producer`: 生产商
- `Symptom`: 症状
- `Cure`: 疗法
""")
        
        # 关系类型说明
        md.append("## 🔗 关系类型说明\n")
        md.append("""系统支持的关系类型：
- `belongs_to`: 属于
- `common_drug`: 常用药
- `do_eat`: 宜吃
- `drugs_of`: 药物治疗
- `need_check`: 需要检查
- `no_eat`: 忌吃
- `recommand_drug`: 推荐药
- `recommand_eat`: 推荐食物
- `has_symptom`: 症状
- `acompany_with`: 并发症
- `cure_way`: 治疗方法
""")
        
        md.append("\n*文档由 API 文档生成器自动生成*\n")
        
        return "\n".join(md)
    
    def _get_module_title(self, module_name: str) -> str:
        """获取模块标题"""
        titles = {
            'auth': '认证接口',
            'admin': '管理员接口',
            'kg_management': '知识图谱接口',
            'qa': '问答接口',
            'crawler': '爬虫接口',
            'search': '搜索接口'
        }
        return titles.get(module_name, f'{module_name}接口')
    
    def _get_module_emoji(self, module_name: str) -> str:
        """获取模块对应的 emoji"""
        emojis = {
            'auth': '🔐',
            'admin': '👨‍💼',
            'kg_management': '🗂️',
            'qa': '🤖',
            'crawler': '🕷️',
            'search': '🔍'
        }
        return emojis.get(module_name, '📌')
    
    def _get_anchor(self, title: str) -> str:
        """将标题转换为锚点"""
        # 移除 emoji 和空格
        anchor = re.sub(r'[^\w\u4e00-\u9fff]', '', title)
        return anchor.lower()
    
    def save_document(self, output_path: str = "docs/API 接口文档.md"):
        """保存文档到文件"""
        md_content = self.generate_markdown()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"📄 文档已保存到：{output_file.absolute()}")
    
    def check_changes(self, existing_doc_path: str = "docs/API 接口文档.md") -> bool:
        """检查是否有接口变更"""
        if not Path(existing_doc_path).exists():
            return True
        
        # 生成新的文档内容
        new_content = self.generate_markdown()
        
        # 读取现有文档
        with open(existing_doc_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # 比较（忽略时间戳和版本号）
        new_normalized = re.sub(r'> \*\*最后更新\*\*: .*\n', '', new_content)
        existing_normalized = re.sub(r'> \*\*最后更新\*\*: .*\n', '', existing_content)
        
        return new_normalized != existing_normalized


def main():
    """主函数"""
    print("=" * 60)
    print("API 文档自动生成器")
    print("=" * 60)
    print()
    
    generator = APIDocGenerator()
    
    # 扫描 API 文件
    generator.scan_api_files()
    
    # 检查是否有变更
    has_changes = generator.check_changes()
    
    if has_changes:
        print("🔄 检测到接口变更，正在更新文档...")
        generator.save_document()
        print("✅ 文档更新完成！")
    else:
        print("✨ 接口无变更，文档无需更新")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
