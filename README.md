# 期权策略分析平台

基于 LongPort OpenAPI 的期权数据分析工具，提供期权链查看、OI 分布图表和加权平均价计算功能。

## 功能特性

- 📈 **期权链分析**: 查看特定期权到期日的完整期权链数据
- 📊 **OI 分布图表**: 可视化展示 Call/Put 持仓量分布
- 🧮 **加权平均价计算**: 
  - Call 期权加权平均行权价
  - Put 期权加权平均行权价
  - 整体 OI 重心
- 📥 **数据导出**: 支持 CSV 格式下载

## 计算公式

### 1. Call 期权加权平均行权价
```
Call WgtAvg = Σ(Ki × CallOIi) / Σ(CallOIi)
```

### 2. Put 期权加权平均行权价
```
Put WgtAvg = Σ(Ki × PutOIi) / Σ(PutOIi)
```

### 3. 整体 OI 重心
```
All WgtAvg = Σ(Ki × (CallOIi + PutOIi)) / Σ(CallOIi + PutOIi)
```

其中：
- Ki: 第 i 个行权价
- CallOIi: 对应行权价的 Call 未平仓合约数
- PutOIi: 对应行权价的 Put 未平仓合约数

## 安装与运行

### 1. 环境要求
- Python 3.8+
- LongPort API 账号

### 2. 安装依赖
```bash
python3 -m venv venv
source venv/bin/activate
pip install longport streamlit plotly pandas numpy python-dotenv
```

### 3. 配置 API 密钥
编辑 `.env` 文件，填入你的 LongPort API 凭证：
```env
LONGPORT_APP_KEY=your_app_key
LONGPORT_APP_SECRET=your_app_secret
LONGPORT_ACCESS_TOKEN=your_access_token
```

### 4. 运行应用
```bash
./run.sh
```

或在 Windows 上：
```bash
venv\Scripts\activate
streamlit run app.py
```

应用将在 http://localhost:8501 启动

## 使用说明

1. 打开浏览器访问 http://localhost:8501
2. 点击左侧「连接 API」按钮
3. 输入股票代码（如 NVDA, AAPL, TSLA）
4. 选择期权到期日
5. 点击「获取数据」查看分析结果

## 项目结构

```
option/
├── app.py                 # 主应用入口
├── src/
│   ├── __init__.py
│   ├── config.py          # 配置文件
│   ├── longport_client.py # LongPort API 客户端
│   ├── calculations.py    # 计算逻辑
│   └── charts.py          # 图表组件
├── .env                   # 环境变量（API 密钥）
├── run.sh                 # 启动脚本
└── README.md
```

## 技术栈

- **后端**: Python + LongPort OpenAPI
- **前端**: Streamlit
- **图表**: Plotly
- **数据处理**: Pandas, NumPy

## 许可证

MIT License

## 免责声明

本工具仅供学习和研究使用，不构成投资建议。使用本工具进行的投资决策风险自负。
