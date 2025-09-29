#!/usr/bin/env python3
"""
OpenAPI 到 Mintlify MDX 转换器（简化版）
自动将 OpenAPI YAML 文件转换为 Mintlify MDX 格式的 API 文档页面
使用标准库，无需额外依赖
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

def parse_yaml_basic(content: str) -> Dict[str, Any]:
    """简单的 YAML 解析器（仅用于基本结构）"""
    # 这是一个简化的解析器，仅用于提取基本的路径信息
    lines = content.split('\n')
    paths = {}
    current_path = None
    current_method = None
    current_operation = {}
    in_tags = False
    tags = []

    for line in lines:
        line_stripped = line.strip()

        # 匹配路径
        if line_stripped.startswith('/') and line_stripped.endswith(':'):
            if current_path and current_method:
                if current_path not in paths:
                    paths[current_path] = {}
                paths[current_path][current_method] = current_operation

            current_path = line_stripped[:-1]  # 移除末尾的冒号
            current_method = None
            current_operation = {}
            in_tags = False
            tags = []

        # 匹配 HTTP 方法
        elif line_stripped in ['get:', 'post:', 'put:', 'delete:', 'patch:']:
            if current_path and current_method:
                if current_path not in paths:
                    paths[current_path] = {}
                paths[current_path][current_method] = current_operation

            current_method = line_stripped[:-1]  # 移除末尾的冒号
            current_operation = {}
            in_tags = False
            tags = []

        # 匹配 tags 开始
        elif line_stripped == 'tags:':
            in_tags = True
            tags = []

        # 匹配 tags 内容
        elif in_tags and line_stripped.startswith('- '):
            tag_name = line_stripped[2:].strip()
            tags.append(tag_name)

        # 其他字段结束 tags 解析
        elif line_stripped and not line_stripped.startswith('- ') and not line_stripped.startswith(' ') and in_tags:
            in_tags = False
            current_operation['tags'] = tags

        # 匹配 summary
        elif line_stripped.startswith('summary:'):
            if in_tags:
                in_tags = False
                current_operation['tags'] = tags
            summary = line_stripped[8:].strip().strip('\'"')
            current_operation['summary'] = summary

        # 匹配 description
        elif line_stripped.startswith('description:'):
            if in_tags:
                in_tags = False
                current_operation['tags'] = tags
            desc = line_stripped[11:].strip().strip('\'"')
            current_operation['description'] = desc

    # 处理最后一个操作
    if current_path and current_method:
        if in_tags:
            current_operation['tags'] = tags
        if current_path not in paths:
            paths[current_path] = {}
        paths[current_path][current_method] = current_operation

    return {'paths': paths}

def load_openapi_spec(file_path: str) -> Dict[str, Any]:
    """加载 OpenAPI 规范文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return parse_yaml_basic(content)

def sanitize_filename(name: str) -> str:
    """清理文件名，移除特殊字符"""
    # 移除特殊字符，保留中文、英文、数字和连字符
    name = re.sub(r'[^\w\u4e00-\u9fff\-]', '-', name)
    # 移除多余的连字符
    name = re.sub(r'-+', '-', name)
    # 移除开头和结尾的连字符
    name = name.strip('-')
    return name.lower()

def get_endpoint_category(path: str, tags: List[str]) -> str:
    """根据标签和路径确定模型分类"""
    # 如果有标签，优先使用标签确定分类
    if tags:
        main_tag = tags[0].lower()  # 使用第一个标签

        # 提取主要模型名称
        if 'openai' in main_tag:
            if 'gpt 4o' in main_tag:
                return 'openai-gpt4o'
            elif 'gpt' in main_tag or 'reasoning' in main_tag:
                return 'openai-gpt'
            elif 'audio' in main_tag:
                return 'openai-audio'
            else:
                return 'openai'
        elif 'claude' in main_tag:
            return 'claude'
        elif 'gemini' in main_tag:
            if 'veo3' in main_tag or 'video' in main_tag:
                return 'gemini-veo'
            else:
                return 'gemini'
        elif 'grok' in main_tag:
            return 'grok'
        elif 'midjourney' in main_tag:
            return 'midjourney'
        elif 'suno' in main_tag:
            return 'suno'
        elif 'kling' in main_tag:
            return 'kling'
        elif 'runway' in main_tag:
            return 'runway'
        elif 'ideogram' in main_tag:
            return 'ideogram'
        elif 'flux' in main_tag:
            return 'flux'
        elif 'doubao' in main_tag:
            return 'doubao'
        elif 'higgsfield' in main_tag:
            return 'higgsfield'
        elif 'qwen' in main_tag:
            return 'qwen'
        elif 'minimax' in main_tag:
            return 'minimax'

    # 如果没有标签或无法从标签识别，使用路径判断
    path_lower = path.lower()

    if '/chat/' in path_lower:
        return 'openai-gpt'
    elif '/images/' in path_lower:
        return 'image-models'
    elif '/audio/' in path_lower:
        return 'audio-models'
    elif '/veo/' in path_lower:
        return 'gemini-veo'
    elif '/mj/' in path_lower:
        return 'midjourney'
    elif 'gemini' in path_lower:
        return 'gemini'
    elif '/upload/' in path_lower or '/files' in path_lower:
        return 'file-services'
    elif '/task' in path_lower:
        return 'task-services'
    else:
        return 'other'

def generate_endpoint_mdx(path: str, method: str, operation: Dict[str, Any]) -> str:
    """为单个端点生成 MDX 内容"""

    # 获取基本信息
    summary = operation.get('summary', f'{method.upper()} {path}')
    description = operation.get('description', f'{method.upper()} {path} 接口')
    tags = operation.get('tags', [])

    # 构建 OpenAPI 引用
    openapi_ref = f'"{method.upper()} {path}"'

    # 生成搜索关键词
    search_keywords = []
    search_keywords.extend(tags)  # 添加标签作为关键词
    search_keywords.append(method.upper())  # 添加HTTP方法

    # 从路径提取关键词
    path_parts = [part for part in path.split('/') if part and not part.startswith('v')]
    search_keywords.extend(path_parts)

    # 从summary提取关键词
    if summary:
        search_keywords.extend(summary.split())

    # 去重并清理关键词
    search_keywords = list(set([kw.strip().lower() for kw in search_keywords if kw.strip()]))
    keywords_str = ', '.join(search_keywords)

    # 增强描述信息
    enhanced_description = description
    if tags:
        main_tag = tags[0]
        if 'openai' in main_tag.lower():
            enhanced_description += " - OpenAI API兼容接口"
        elif 'gemini' in main_tag.lower():
            enhanced_description += " - Google Gemini模型接口"
        elif 'midjourney' in main_tag.lower():
            enhanced_description += " - Midjourney图像生成接口"
        elif 'suno' in main_tag.lower():
            enhanced_description += " - Suno AI音乐生成接口"

    # 生成 frontmatter
    frontmatter = f"""---
title: "{summary}"
description: "{enhanced_description}"
openapi: {openapi_ref}
mode: "wide"
---

<Info>
**搜索关键词**: {keywords_str}
</Info>

"""

    # 生成主要内容
    content = f"""# {summary}

{enhanced_description}

## 接口信息

- **请求方法**: `{method.upper()}`
- **接口路径**: `{path}`
- **认证方式**: Bearer Token
- **标签**: {', '.join(tags) if tags else '无'}

## 认证说明

请在请求头中包含有效的 Bearer Token：

```bash
Authorization: Bearer YOUR_API_KEY
```

## 使用说明

使用下方的交互式 API 文档来测试此接口。你可以：

1. 在右侧面板中输入请求参数
2. 点击"Try it"按钮发送请求
3. 查看实时的响应结果

## 示例代码

### cURL 示例

```bash
curl -X {method.upper()} "http://129.226.58.30{path}" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"
```

### Python 示例

```python
import requests

url = "http://129.226.58.30{path}"
headers = {{
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}}

response = requests.{method.lower()}(url, headers=headers)
print(response.json())
```

### JavaScript 示例

```javascript
const response = await fetch('http://129.226.58.30{path}', {{
  method: '{method.upper()}',
  headers: {{
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  }}
}});

const data = await response.json();
console.log(data);
```

## 相关接口

搜索相关标签: {', '.join([f'`{tag}`' for tag in tags]) if tags else '无'}

"""

    return frontmatter + content

def create_directory_structure(base_path: str, categories: set) -> None:
    """创建目录结构"""
    base = Path(base_path)
    for category in categories:
        category_path = base / category
        category_path.mkdir(parents=True, exist_ok=True)

def generate_navigation_config(endpoints_by_category: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
    """生成导航配置"""

    category_names = {
        'openai': 'OpenAI',
        'openai-gpt': 'OpenAI GPT Series',
        'openai-gpt4o': 'OpenAI GPT-4o',
        'openai-audio': 'OpenAI Audio',
        'claude': 'Claude',
        'gemini': 'Gemini',
        'gemini-veo': 'Gemini Veo Video',
        'grok': 'Grok',
        'midjourney': 'Midjourney',
        'suno': 'Suno Music',
        'kling': 'Kling Video',
        'runway': 'Runway',
        'ideogram': 'Ideogram',
        'flux': 'Flux',
        'doubao': 'Doubao',
        'higgsfield': 'Higgsfield',
        'qwen': 'Qwen',
        'minimax': 'MiniMax',
        'image-models': 'Image Generation Models',
        'audio-models': 'Audio Processing Models',
        'file-services': 'File Services',
        'task-services': 'Task Management',
        'other': 'Other APIs'
    }

    navigation_groups = []

    for category, endpoints in endpoints_by_category.items():
        if not endpoints:
            continue

        group_name = category_names.get(category, category.title())
        pages = []

        for endpoint in endpoints:
            pages.append(f"api-reference/{category}/{endpoint['filename']}")

        navigation_groups.append({
            "group": group_name,
            "pages": pages
        })

    return navigation_groups

def main():
    """主函数"""
    # 配置路径
    openapi_file = "openapi.yaml"
    output_dir = "api-reference"

    print("🚀 开始生成 API 文档...")

    # 加载 OpenAPI 规范
    print("📖 加载 OpenAPI 规范...")
    try:
        spec = load_openapi_spec(openapi_file)
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 {openapi_file}")
        return
    except Exception as e:
        print(f"❌ 错误：解析文件失败 {e}")
        return

    # 解析端点
    paths = spec.get('paths', {})
    endpoints_by_category = {}
    all_categories = set()

    print(f"📝 发现 {len(paths)} 个 API 端点")

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method in ['get', 'post', 'put', 'delete', 'patch']:
                # 确定分类
                tags = operation.get('tags', [])
                category = get_endpoint_category(path, tags)
                all_categories.add(category)

                # 生成文件名
                summary = operation.get('summary', f'{method}-{path}')
                filename = sanitize_filename(summary)

                # 确保文件名不为空
                if not filename:
                    filename = f"{method}-{path.replace('/', '-').strip('-')}"
                    filename = sanitize_filename(filename)

                # 确保文件名唯一
                base_filename = filename
                counter = 1
                while any(ep['filename'] == filename for ep_list in endpoints_by_category.values() for ep in ep_list):
                    filename = f"{base_filename}-{counter}"
                    counter += 1

                # 添加到分类
                if category not in endpoints_by_category:
                    endpoints_by_category[category] = []

                endpoints_by_category[category].append({
                    'path': path,
                    'method': method,
                    'operation': operation,
                    'filename': filename,
                    'summary': summary
                })

    # 创建目录结构
    print("📁 创建目录结构...")
    create_directory_structure(output_dir, all_categories)

    # 生成 MDX 文件
    print("✍️  生成 MDX 文件...")
    total_files = 0

    for category, endpoints in endpoints_by_category.items():
        print(f"  📂 处理分类: {category}")
        for endpoint in endpoints:
            # 生成 MDX 内容
            mdx_content = generate_endpoint_mdx(
                endpoint['path'],
                endpoint['method'],
                endpoint['operation']
            )

            # 写入文件
            file_path = Path(output_dir) / category / f"{endpoint['filename']}.mdx"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(mdx_content)

            total_files += 1
            print(f"    ✓ {file_path}")

    # 生成导航配置
    print("🧭 生成导航配置...")
    navigation_groups = generate_navigation_config(endpoints_by_category)

    # 输出导航配置到文件
    nav_config_file = "generated-navigation.json"
    with open(nav_config_file, 'w', encoding='utf-8') as f:
        json.dump(navigation_groups, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 完成！")
    print(f"  📄 生成了 {total_files} 个 API 文档页面")
    print(f"  📂 创建了 {len(all_categories)} 个分类目录：{', '.join(sorted(all_categories))}")
    print(f"  🧭 导航配置已保存到 {nav_config_file}")
    print(f"\n下一步：")
    print(f"1. 查看生成的文档文件")
    print(f"2. 将 {nav_config_file} 中的内容添加到 mint.json 的 navigation 部分")
    print(f"3. 运行 mintlify dev 测试生成的文档")

if __name__ == "__main__":
    main()