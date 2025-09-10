# 🤖 AI Insights (Heuristic Model)

Short overview of the AI/"model" functionality implemented in this project and what works today.

## What it is
- A lightweight, heuristic-based module that provides absence/WFH risk insights for managers.
- There is no trained machine learning model yet. The logic uses patterns mined from historical attendance data.

## Where it lives (code)
- utils.py
  - predict_absence_risk(vendor_id, days_ahead=7)
  - generate_ai_insights(manager_id, prediction_window_days=7)

## What it does
- Looks back 90–120 days of DailyStatus records for each vendor on a manager’s team.
- Computes:
  - Leave rate and WFH rate
  - Recent leave bursts (last ~14 days)
  - Day-of-week patterns (e.g., higher leave/WFH on specific weekdays)
  - Skips weekends and system-defined holidays
- Produces per-vendor predictions with:
  - Predicted date (next likely working day within the window)
  - Likelihood percentage
  - Risk level (Low/Medium/High/Critical)
  - Human-readable reasons/factors
  - Recommendation (e.g., Urgent Intervention, Schedule Backup)

## What’s working today (in-product)
- Manager UI page with insights
  - GET /manager/ai-insights
- Export AI report (Excel or JSON)
  - GET /api/ai/report?window=7&format=excel|json
- Configure analysis schedule (stored in system configuration)
  - POST /api/ai/schedule
- View recent related logs (uses AuditLog as a simple source)
  - GET /api/ai/model-logs
- Emergency enable/disable toggle (persists to configuration)
  - POST /api/ai/override with { enable: true|false }

## What is placeholder/not implemented
- No ML training pipeline yet (the “Re-train Model” button is a UI placeholder).
- No model artifact storage or versioning.
- Displayed performance metrics are illustrative.

## How it works (brief)
1) Base risk (predict_absence_risk)
- Uses last 90 days to compute leave_rate, wfh_rate, and recent leaves.
- Assigns a base risk score using thresholds if the rates are high or recent leaves cluster.

2) Pattern enrichment (generate_ai_insights)
- Scans last ~120 days for day-of-week patterns (higher leave/WFH on specific weekdays).
- Prefers a predicted date that matches the strongest weekday pattern within the window; otherwise picks the next working day.
- Combines base risk with pattern strength to produce a likelihood and risk tier, plus a recommendation.

## Quick usage
- Visit the UI: /manager/ai-insights
- Export Excel report: /api/ai/report?window=7&format=excel
- Export JSON report: /api/ai/report?window=7&format=json
- Set schedule: POST /api/ai/schedule (form or JSON) with schedule=daily|weekly|monthly
- See logs: /api/ai/model-logs
- Toggle override: POST /api/ai/override with enable=true|false

## Future enhancements (suggested)
- Replace heuristics with a real ML pipeline (feature engineering, training, evaluation).
- Track and display live model performance metrics (precision/recall by risk tier).
- Add automated retraining and model versioning.
- Expand features (e.g., vendor tenure, seasonality, cross-team context).

