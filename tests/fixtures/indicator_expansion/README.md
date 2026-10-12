# 指标独立参考数据

`quotes.csv`、`smi.json`、`pmo.json` 来自 [Stock.Indicators 固定提交](https://github.com/DaveSkender/Stock.Indicators/tree/e92f641d87ebf719b1f7a5a58744b8db781a2ba3/tests/Library/TestData)，保留原始数值。Apache-2.0 许可全文见相邻 LICENSE.stock-indicators；不安装或调用该库生成预期结果。

其他小样例由测试按公开公式手算，状态机另核对该提交的 AtrStopSeriesTests 与 VolatilityStopSeriesTests 中固定预期值；本地 Volatility Stop 首次反转前保持无效，避免上游事后清除历史。
