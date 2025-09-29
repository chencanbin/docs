# Mintlify 文档部署指南

## 方法一：Vercel 部署

### 1. 安装 Vercel CLI
```bash
npm i -g vercel
```

### 2. 在项目根目录创建 vercel.json
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "out",
  "installCommand": "npm install",
  "framework": "nextjs"
}
```

### 3. 部署
```bash
vercel --prod
```

## 方法二：Netlify 部署

### 1. 安装 Netlify CLI
```bash
npm install -g netlify-cli
```

### 2. 部署
```bash
netlify deploy --prod --dir .
```

## 方法三：GitHub Pages

### 1. 创建 GitHub Actions 工作流
在 `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'

    - name: Install dependencies
      run: npm install -g @mintlify/cli

    - name: Build
      run: mintlify build

    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./out
```

## 方法四：Docker 部署

### 1. 创建 Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY . .

RUN npm install -g @mintlify/cli
EXPOSE 3000

CMD ["mintlify", "dev", "--host", "0.0.0.0"]
```

### 2. 构建和运行
```bash
docker build -t docs .
docker run -p 3000:3000 docs
```

## 搜索功能说明

- **本地开发**: 搜索功能不可用
- **生产环境**: 自动启用全文搜索
- **配置完成**: 已在 mint.json 中配置搜索提示

部署后搜索功能将完全可用！