# GitHub 上传指南

## 方法一：通过命令行上传（推荐）

### 1. 创建 GitHub 仓库
1. 访问 https://github.com/new
2. 输入仓库名称，例如 `option-strategy-platform`
3. 选择 **Public**（公开）或 **Private**（私有）
4. 不要勾选 "Initialize this repository with a README"
5. 点击 **Create repository**

### 2. 连接本地仓库到 GitHub

在终端中执行以下命令（将 `YOUR_USERNAME` 替换为你的 GitHub 用户名）：

```bash
cd /Users/chen/Documents/trae_projects/option

# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/option-strategy-platform.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 3. 输入 GitHub 凭据
- 如果使用 HTTPS，需要输入 GitHub 用户名和密码
- 如果使用 SSH，需要配置 SSH 密钥（见下文）

---

## 方法二：使用 GitHub Desktop（图形界面）

### 1. 下载安装 GitHub Desktop
https://desktop.github.com/

### 2. 添加本地仓库
1. 打开 GitHub Desktop
2. 点击 **File** → **Add Local Repository**
3. 选择 `/Users/chen/Documents/trae_projects/option` 文件夹
4. 点击 **Add Repository**

### 3. 发布到 GitHub
1. 点击 **Publish repository**
2. 输入仓库名称
3. 选择 Public 或 Private
4. 点击 **Publish Repository**

---

## 方法三：使用 VS Code

### 1. 安装 GitHub 扩展
在 VS Code 中搜索并安装 "GitHub Pull Requests and Issues"

### 2. 登录 GitHub
点击左侧活动栏的 GitHub 图标，登录你的 GitHub 账号

### 3. 发布仓库
1. 点击左侧源代码管理图标
2. 点击 **Publish to GitHub**
3. 选择 Public 或 Private
4. 点击 **Publish**

---

## SSH 密钥配置（可选但推荐）

### 1. 生成 SSH 密钥
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### 2. 添加密钥到 SSH 代理
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 3. 复制公钥到 GitHub
```bash
cat ~/.ssh/id_ed25519.pub
```
复制输出内容，然后：
1. 访问 https://github.com/settings/keys
2. 点击 **New SSH key**
3. 粘贴公钥，点击 **Add SSH key**

### 4. 使用 SSH 地址
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/option-strategy-platform.git
```

---

## 常用 Git 命令

```bash
# 查看状态
git status

# 添加所有更改
git add .

# 提交更改
git commit -m "描述信息"

# 推送到 GitHub
git push

# 拉取最新代码
git pull

# 查看提交历史
git log
```

---

## 注意事项

1. **`.env` 文件** - 包含 API 密钥，已添加到 `.gitignore`，不会上传到 GitHub
2. **`venv/` 目录** - 虚拟环境，已添加到 `.gitignore`
3. **`test_api.py`** - 测试文件，已添加到 `.gitignore`

如需分享项目，其他用户需要：
1. 克隆仓库
2. 创建自己的 `.env` 文件并填入 API 密钥
3. 创建虚拟环境并安装依赖

```bash
git clone https://github.com/YOUR_USERNAME/option-strategy-platform.git
cd option-strategy-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
