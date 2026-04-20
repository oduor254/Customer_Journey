# Dashboard Quick Guide: Using the New WhatsApp Engagement Layer

**Updated: March 29, 2026**

---

## 📊 For Your Teams

### 🎯 MANAGEMENT - Executive Overview

**Key Questions You Can Now Answer:**

1. **"Are we capturing leads?"**
   - Look at: **Total Leads** (Funnel Stage 1)
   - Action: If trending down, marketing budget may be ineffective

2. **"Are we engaging captured leads?"**
   - Look at: **Engagement Rate** 
   - Target: Aim for 40-50% of leads in WhatsApp
   - Action: If <30%, your community team isn't qualifying leads effectively

3. **"Are engaged leads actually buying?"**
   - Look at: **Engagement-to-Conversion Rate**
   - Target: Aim for 30-40% of engaged leads to purchase
   - Action: If <20%, sales team needs better process/follow-up

4. **"How long is our sales cycle?"**
   - Look at: **Avg Days Engagement→Purchase**
   - Compare: Against your industry standard
   - Action: If >30 days, identify bottlenecks

5. **"Where are we losing money?"**
   - Look at: **Drop Rate** between funnel stages
   - Highest loss: Usually between "Engaged" → "First Purchase"
   - Action: Investigate sales process gaps

**Monthly Management Report Template:**
```
Month: March 2026
├─ Total Leads Acquired: 5,200
├─ Engagement Rate: 42% (2,184 engaged)
├─ Engagement→Conversion: 35.7% (780 converted)
├─ Overall Conversion Rate: 15% (780 of 5,200)
├─ Avg Sales Cycle: 14.5 days
├─ Revenue Generated: $125,000
└─ Cost per Customer: $160
```

---

### 👨‍💼 SALES TEAM - Pipeline & Performance

**Key Questions You Can Now Answer:**

1. **"Who are my hottest leads right now?"**
   - Look at: **Active Engaged** customers (Stage 3)
   - These had activity in last 30 days = ready to buy
   - Action: Prioritize follow-up on these leads

2. **"Which sales activities work best?"**
   - Look at: **Activity Effectiveness** table
   - Example breakdown:
     - Demo Scheduled: 40% conversion rate ← BEST
     - Quote Sent: 35% conversion rate
     - Follow-up Call: 20% conversion rate ← NEEDS WORK
   - Action: Coach team on demo scheduling technique

3. **"Which branches perform best?"**
   - Look at: **Branch Performance** section
   - Compare: Conversion rates and avg revenue per customer
   - Action: Replicate best-performing branch's process to others

4. **"How long does it take to close?"**
   - Look at: **Avg Days to Purchase** by branch/platform
   - Compare with: Your KPI targets
   - Action: If >21 days, identify delays in your process

5. **"Who's falling through the cracks?"**
   - Look at: **Funnel Drop Rates**
   - Highest drop between: Engaged → Active Engaged
   - Action: Check if follow-up frequency is sufficient

**Weekly Sales Standup Metrics:**
```
Week of March 24-30, 2026
├─ New Engaged Leads (Last 7 days): 450
├─ Active Engaged (Hot Now): 280
├─ Converted This Week: 95
├─ Avg Days to Convert: 15 days
└─ Top Performer Activity: Demo Scheduled (42% conversion)
```

**Sales Coaching Insight:**
- If a rep has leads but low conversion:
  - Check their activity (are they scheduling demos?)
  - Review funnel: where are their leads getting stuck?
  - Coach on best practices from high-conversion reps

---

### 📱 MARKETING TEAM - Channel Performance

**Key Questions You Can Now Answer:**

1. **"Which channels drive the best leads?"**
   - Look at: **By Source** in engagement_analytics
   - Compare: Engaged count × Conversion rate
   - Example:
     - Instagram: 900 engaged → 37.8% conversion = 340 customers
     - Facebook: 600 engaged → 28% conversion = 168 customers
   - Action: Allocate more budget to Instagram

2. **"Are my social media clicks converting to conversations?"**
   - Look at: **Engagement Rate** back to total leads
   - If Instagram drives 900 engaged from 2,400 total leads:
     - Engagement Rate from Instagram = 37.5% (good!)
   - Action: If <20%, revise messaging or targeting

3. **"Which content/offer is driving engagement?"**
   - Work with sales team: Map campaigns to **Source data**
   - Example: "Free Consultation Offer" → Instagram → 40% engagement rate
   - Action: Double down on this content/offer

4. **"What's the quality of engagement by channel?"**
   - Look at: **Engagement→Conversion Rate by Source**
   - Instagram engaged → 37.8% conversion (HIGH QUALITY)
   - TikTok engaged → 22% conversion (NEEDS IMPROVEMENT)
   - Action: Revise TikTok strategy or audience targeting

5. **"Are we reaching the right audience?"**
   - Look at: **Avg Customer Value by Channel**
   - If Instagram customers spend more → quality audience
   - If Facebook customers spend less → wrong audience
   - Action: Adjust targeting/messaging per channel

**Marketing Performance Report Template:**
```
March 2026 Performance
├─ Total Impressions: 250,000
├─ Click-through Rate: 2.1%
├─ Leads Generated: 5,200
│
├─ By Channel:
│  ├─ Instagram: 2,400 leads → 37.5% engagement → 340 converted
│  ├─ Facebook: 1,600 leads → 28% engagement → 128 converted
│  ├─ TikTok: 800 leads → 18% engagement → 72 converted
│  └─ Twitter: 400 leads → 15% engagement → 24 converted
│
├─ Cost per Engaged Lead: $8.50
├─ Cost per Customer: $156
└─ ROAS (Return on Ad Spend): 3.2x
```

---

## 📈 Interpreting the 5-Stage Funnel

```
STAGE          | MEANING                    | ACTION IF LOW
───────────────┼────────────────────────────┼──────────────────────────
Total Leads    | Marketing volume           | Need more leads/budget
Engaged        | % reaching WhatsApp        | Community team not qualifying
Active Engaged | Recent activity (hot)      | Sales team not following up
Converted      | Made 1st purchase          | Sales process broken
Loyal          | Repeat buyers              | Customer success/retention issue
```

**Example Analysis:**
```
Total Leads:       5,000 (100%)
    ↓ (58% drop)
Engaged:           2,100 (42%)  ← ISSUE: Too many leads lost here
    ↓ (68% drop of engaged)
Active Engaged:      680 (13.6%)
    ↓ (15% drop)
Converted:           780 (15.6% of initial) ✓ GOOD
    ↓ (35% drop)
Loyal:              507 (65% of converted) ✓ GOOD

INSIGHT: Main bottleneck is engagement (58% don't reach WhatsApp)
  → Marketing may be sending wrong audience
  → Community team needs more resources
```

---

## 🎯 Actionable Dashboards to Request from Tech Team

### Dashboard 1: Executive KPI Cards
```
┌─────────────────────────────────────┐
│ Engagement Rate: 42%                │ ← Text green/red if vs target
│ vs Target: 40%  [↑ Good]            │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Engagement→Conversion: 35.7%        │
│ vs Last Month: 32.1% [↑ Improving]  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Avg Days to Purchase: 14.5 days     │
│ vs Target: 14 days [↓ Close]        │
└─────────────────────────────────────┘
```

### Dashboard 2: Source Performance Matrix
```
┌──────────┬──────────┬───────────┬──────────────┐
│ Source   │ Engaged  │ Converted │ Conv. Rate   │
├──────────┼──────────┼───────────┼──────────────┤
│Instagram │   900    │    340    │  37.8% ★★★★★│
│Facebook  │   600    │    168    │  28.0% ★★★☆☆│
│TikTok    │   800    │   176     │  22.0% ★★☆☆☆│
│Twitter   │   100    │    16     │  16.0% ★☆☆☆☆│
└──────────┴──────────┴───────────┴──────────────┘
```

### Dashboard 3: Activity Effectiveness
```
┌─────────────────┬────────┬─────────┬──────────┐
│ Activity        │ Engaged│Converted│Conv. %   │
├─────────────────┼────────┼─────────┼──────────┤
│Demo Scheduled   │  450   │   180   │ 40.0%  ✅│
│Quote Sent       │  800   │   280   │ 35.0%  ✅│
│Callback Booked  │  600   │   180   │ 30.0%  ✓ │
│Follow-up Call   │  500   │   75    │ 15.0%  ❌│
│Text Only        │  250   │   12    │  4.8%  ❌│
└─────────────────┴────────┴─────────┴──────────┘

FINDING: Demos & quotes drive sales. Text-only ineffective.
ACTION: Shift focus to demo scheduling. Reduce text-only follow-ups.
```

### Dashboard 4: 5-Stage Funnel with Drop Rates
```
100% ╔════════════════════════╗ TOTAL LEADS (5,000)
     ║                        ║
     ║    ⬇ 58% DROP         ║
     ║                        ║
42%  ╠════════════════════╉   ║ ENGAGED (2,100) 
     ║              ⬇ 68% ║   ║
     ║              DROP  ║   ║
     ║              ║     ║   ║
13%  ╠════════╉      ║   ║   ║ ACTIVE ENGAGED (680)
     ║    ⬇ 15%      ║   ║   ║
     ║    DROP       ║   ║   ║
     ║    ║          ║   ║   ║
15%  ╠════════════════════╉   ║ CONVERTED (780)
     ║         ⬇ 35% DROP    ║
     ║              ║        ║
     ║              ║        ║
10%  ╚═════════════════⬇═════╝ LOYAL (507)
```

---

## 🔄 Using the Dashboard for Decision Making

### Scenario 1: Declining Engagement Rate

**Observation:** Engagement rate dropped from 45% to 38% month-over-month

**Analysis:**
1. Check: What changed in marketing? (Different audience? New campaign?)
2. Check: Did community team capacity decrease?
3. Check: Are new leads different quality? (Compare by source)

**Action:**
- If campaign change: Revert to previous targeting
- If team capacity: Hire/allocate resources
- If quality issue: Marketing needs better lead qualification

---

### Scenario 2: Low Conversion Rate Despite High Engagement

**Observation:** 48% engagement rate but only 20% engagement→conversion

**Analysis:**
- Plenty of people are interested (high engagement)
- But sales team isn't closing them (low conversion-from-engagement)
- This suggests: **Sales process problem, not marketing problem**

**Action:**
1. Audit sales activities: Which activities drive conversions?
2. Compare high-conversion vs low-conversion reps
3. Identify best practices and coach team
4. Check: Are follow-ups happening quickly enough?

---

### Scenario 3: Channel Underperforming

**Observation:** Facebook engagement rate only 22% vs Instagram 38%

**Analysis:**
- Facebook leads are less interested (lower engagement)
- OR less likely to use WhatsApp
- Suggests: Wrong audience or wrong messaging for Facebook

**Action:**
1. Review Facebook audience targeting
2. Test different ad copy/offers
3. Consider reallocating budget to Instagram
4. If engagement rates improve with A/B testing, implement winner

---

## 📞 Monthly Review Checklist

Use this checklist for your monthly business review:

```
☐ Total Leads: Increasing? Stable? Decreasing?
  Action if down: Review marketing budget and campaigns

☐ Engagement Rate: Is % of leads reaching WhatsApp on target?
  Action if low: Check community team capacity and qualification process

☐ Engagement→Conversion Rate: Are engaged leads buying?
  Action if low: Audit sales activities and team training

☐ Avg Days to Purchase: Is sales cycle within target?
  Action if high: Identify delays (approval? logistics? decision?)

☐ Repeat Purchase Rate: Are customers coming back?
  Action if low: Review customer satisfaction and post-purchase support

☐ Revenue per Customer: Is it increasing?
  Action: Track by source to identify best customer segments

☐ By Source Performance: Which channels most profitable?
  Action: Increase budget for best performers, reduce low performers

☐ Activity Effectiveness: Which sales activities drive conversions?
  Action: Coach team on best practices; eliminate ineffective activities
```

---

## 🎓 Key Takeaways

**For Management:**
- Engagement and conversion are separate issues (different teams to fix)
- Monitor drop rates between stages to identify bottlenecks
- Use metrics to make data-driven budget allocation decisions

**For Sales:**
- Activity effectiveness shows what works → replicate it
- Active Engaged customers are your hottest leads → prioritize
- Track your conversion rates vs team average

**For Marketing:**
- Source performance shows which channels to invest in
- Engagement rate shows lead quality
- Compare campaign performance to optimize spend

---

## 📧 Getting Help

**Questions?**
1. Check the IMPLEMENTATION_GUIDE.md for technical details
2. Review the Readme.md for metric definitions
3. Visit `/api/refresh` to force data reload if numbers seem stale

**Dashboard not showing new data?**
1. Ensure Whatsapp sheet exists in Google Sheets
2. Confirm columns: DATE, NAME, CONTACT, SOURCE, ACTIVITY, BRANCH
3. Run `/api/refresh` endpoint
4. Hard refresh browser (Ctrl+F5)

---

**Created:** March 29, 2026  
**Status:** Ready for Dashboard Implementation
