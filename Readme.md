# Customer Journey Dashboard 2025

A Flask + HTML/CSS/JS dashboard that analyses your customer journey from
first lead touchpoint → WhatsApp engagement → purchase history → customer loyalty.

---

## 📊 What's New: WhatsApp Engagement Layer

Your dashboard now tracks the complete customer journey:
1. **Lead Acquisition** (Instagram, TikTok, Facebook, etc.)
2. **Engagement** (WhatsApp interactions - NEW!)
3. **Purchase & Loyalty** (Branch transactions)

---

## Folder Structure

```
customer_journey_dashboard/
├── app.py            ← Flask backend
├── index.html        ← Dashboard frontend
├── requirements.txt  ← Python dependencies
└── README.md
```

---

## 1. Prerequisites

- Python 3.9+
- A Google Cloud service account JSON key with the Sheets API enabled
- The key file is already expected at:
  `C:\Users\Oduor\Downloads\JSON Files\retention-484110-9e4520124486.json`

> **Important:** Share your Google Sheet with the service account email
> (found inside the JSON file as `"client_email"`) and grant it **Viewer** access.

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Run the server

```bash
python app.py
```

Open your browser at → **http://localhost:5004**

---

## 4. API Endpoints

| Endpoint           | Description                                  |
|--------------------|----------------------------------------------|
| `GET /`            | Serves the dashboard HTML                    |
| `GET /api/data`    | Returns full analytics JSON (cached)         |
| `GET /api/refresh` | Clears cache and reloads from Sheets         |

---

## 5. Data Structure

### Required Google Sheets

1. **Leads_2025** (Initial lead acquisition)
   - Columns: DATE, NAME, CONTACT, SOURCE, BRANCH, MONTH

2. **Shops** (Purchase history)
   - Columns: DATE, PHONE, PRICE, LOCATION, GENDER, CATEGORY, etc.

3. **Whatsapp** (NEW! Engagement layer)
   - Columns: DATE, NAME, CONTACT, SOURCE, ACTIVITY, BRANCH

---

## 6. Data Matching Logic

Leads, WhatsApp engagement, and purchases are matched using the **last 9 digits of the phone number**.

- `Leads_2025.CONTACT` → normalized → matches `Whatsapp.CONTACT` and `Shops.PHONE`

---

## 7. Key Metrics Explained

### Executive KPIs (Management View)

| Metric | Meaning |
|--------|---------|
| **Total Leads** | All leads from social media |
| **Engagement Rate** | % of leads transferred to WhatsApp |
| **Engagement-to-Conversion** | Of engaged leads, % that purchased |
| **Conversion Rate** | % of all leads that purchased |
| **Avg Time Engagement→Purchase** | How long from WhatsApp contact to first purchase |
| **Repeat Purchase Rate** | % of customers who bought 2+ times |
| **Churn Rate** | % of customers inactive 30+ days |

### Sales Team View (Performance Metrics)

| Metric | Meaning |
|--------|---------|
| **5-Stage Funnel** | Leads → Engaged → Active Engaged → Purchased → Loyal |
| **Activity Effectiveness** | Which WhatsApp activities drive conversions |
| **Days to Purchase** | Average sales cycle by platform/branch |
| **Branch Performance** | Conversion rate and revenue by location |

### Marketing Team View (Channel Performance)

| Metric | Meaning |
|--------|---------|
| **Lead Quality by Source** | Which platform generates best customers |
| **Engagement Rate by Source** | Which platform leads engage most on WhatsApp |
| **Source→Purchase Pipeline** | Instagram leads → WhatsApp engagement → conversion rate |
| **Activity Mix** | Types of WhatsApp interactions happening |

---

## 8. Understanding the 5-Stage Funnel

```
TOTAL LEADS (100%)
    ↓
    └─→ ENGAGED (in WhatsApp) - Drop rate shown
        ↓
        └─→ ACTIVE ENGAGED (last 30 days) - Hot leads
            ↓
            └─→ FIRST PURCHASE - Conversion point
                ↓
                └─→ LOYAL CUSTOMERS (2+ purchases)
```

**How to Read It:**
- **Stage Count**: Number of leads/customers in that stage
- **% of Total**: How many of original leads reach this stage
- **Drop Rate**: % lost between this stage and previous (conversion opportunity!)

---

## 9. WhatsApp Activity Analysis

The dashboard analyzes which **ACTIVITY** types drive conversions:

Examples of activities tracked:
- "Quotation Sent" → Conversion Rate %
- "Product Demo" → Conversion Rate %
- "Follow-up Call" → Conversion Rate %
- "Appointment Scheduled" → Conversion Rate %

**Sales Insight:** Focus on activities with highest conversion rates

---

## 10. Troubleshooting

### "Could not load Whatsapp sheet"
- Ensure your Google Sheet has a "Whatsapp" worksheet
- Verify the service account has access
- The app will continue without WhatsApp data (backward compatible)

### Data not updating
- Clear cache: Visit `/api/refresh` 
- This forces fresh load from Google Sheets

### Slow loading
- First load takes ~20 seconds (Google Sheets API)
- Subsequent loads use local 6-hour cache

---

## 11. Next Steps for Your Team

### For Management
1. Track **Engagement Rate** weekly - Is marketing growing the funnel?
2. Monitor **Churn Rate** - Are we retaining customers?
3. Compare **Branch Performance** - Which location converts best?
4. Analyze **Cost per Customer** - ROI from each channel

### For Sales
1. Identify **Hot Leads** (Active Engaged stage) - prioritize follow-up
2. Track **Activity Effectiveness** - double down on what works
3. Monitor **Days to Purchase** - optimize sales cycle
4. Focus on **Repeat Purchase** - build customer loyalty

### For Marketing
1. **Optimize for Engagement** - Is social content converting to WhatsApp?
2. **Measure Source Quality** - Which platform drives best customers?
3. **Activity Mix** - What types of engagement are happening?
4. **Funnel Improvement** - Where are leads dropping off?

---

## 12. Data Freshness & Caching

- **First load**: ~20 seconds (fetches from Google Sheets)
- **Cached loads**: < 1 second (uses local cache)
- **Cache expires**: 6 hours
- **Manual refresh**: `/api/refresh` endpoint clears cache immediately