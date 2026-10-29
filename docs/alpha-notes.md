# 19th — Private Alpha

> Source: Notion invite page `19th-Private-Alpha` (`403e131c-8be7-8016-8ffa-f86becfc9f28`),
> captured 2026-10-29. Kept here so the repo explains itself without the Notion login.
> Contact phone numbers are left off this copy — they are on the Notion page.

Welcome to the private alpha of 19th.

## Getting started

There are two ways to use 19th: via MCP or API.

### MCP

1. Point your agent at the MCP — recommended prompt:
   `Read https://19th.com/docs/mcp and help me connect to 19th`
   - Or follow the instructions at https://19th.com/mcp
2. Recommended first step: ask your agent what models 19th could train using the context it
   already knows about your work.

### API

1. Go to https://app.19th.com/api-keys and create a **Training API** key.
2. Point your agent at the API docs — recommended prompt:
   `Read https://19th.com/docs/training and help me train a model using the 19th API.`
3. Provide your CSV and say what you want to predict.
4. Submit your data and start training.
5. Get predictions through the API, or download your model to run locally or deploy
   yourself.

## Demo datasets

Provided for poking around before you bring your own data.

| Demo | Goal | Data file |
| --- | --- | --- |
| 🩻 Tumor Diagnosis | Predict whether a tumor sample is malignant or benign from its measurements. | `breast_cancer_diagnostic.csv` |
| 🌌 Exoplanet Detector | Train a planet detector on NASA's Kepler catalog. | `kepler_koi.csv` |
| 👨‍💻 Support Ticket Routing | Classify a banking support message into one of 77 support team categories. | `support_intents.csv` |
| 🚛 Predictive Machine Maintenance | Use readings such as torque and operating time to predict whether a machine is likely to fail. | `machine_failure_binary.csv` |

## Contact

**Max** — max@19th.com
**Spencer** — spencer@19th.com

Founders: founders@19th.com
