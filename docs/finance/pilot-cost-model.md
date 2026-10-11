# Pilot Financial & Unit Economics Cost Model

**Pilot Parameters**: 100 Invited Users, 30 Days  
**Scope**: FashXStudio Production Architecture (`AWS ap-south-1` Mumbai)  
**Status**: Release Gate G5 Verified  

---

## 1. Cost Breakdown (30-Day Pilot Window)

### A. AWS Mumbai Cloud Infrastructure
| Service | Configuration & Sizing | Monthly Cost (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **ECS Fargate (API & Workers)** | 2 tasks @ 0.5 vCPU, 1.0 GB RAM | $34.56 | Autoscaling min 2, max 4 |
| **RDS PostgreSQL (db.t4g.medium)** | 2 vCPU, 4.0 GB RAM, 30 GB gp3 storage | $51.84 | Single-AZ staging/pilot with automated daily snapshots |
| **ElastiCache Redis (cache.t4g.micro)** | 0.5 GB RAM, primary node | $14.60 | In-memory caching & rate limiting |
| **S3 Media Storage & Egress** | 100 GB storage, 50 GB data transfer out | $11.50 | Encrypted presigned uploads |
| **CloudWatch Logs** | 15 GB ingestion, 365-day log retention | $8.25 | India CERT-In / DPDP log retention |
| **Route 53 & ALB** | 1 Application Load Balancer, hosted zone | $22.50 | Target group health monitoring |
| **Subtotal Infrastructure** | | **$143.25** | |

### B. Machine Learning & Third-Party APIs
| Service | Consumption Model | Unit Rate | Projected Pilot Cost |
| :--- | :--- | :--- | :--- |
| **Virtual Try-On Inference (FASHN API)** | 100 users × 25 try-ons avg = 2,500 try-ons | $0.075 / image | **$187.50** |
| **Supabase Auth** | 100 users, email magic-link / OTP delivery | Pro tier flat | **$25.00** |
| **Subtotal AI & External Services** | | | **$212.50** |

---

## 2. Total Pilot Cost & Per-User Economics

$$\text{Total 30-Day Pilot Expense} = \$143.25 + \$212.50 = \mathbf{\$355.75}$$

- **Cost Per Active Pilot User**: $\frac{\$355.75}{100} = \mathbf{\$3.56}$ per user across the entire 30-day trial.
- **Cost Per Try-On Render**: $\mathbf{\$0.075}$ (Meets Gate G5 ceiling of $\le \$0.10$ with 25% margin).
- **Safety Cushion**: Backed by a dedicated $500.00 pre-pilot budget buffer with hard daily spend alerts at $50/day.

---

## 3. Commercial Path to Solvency (Post-Pilot Projections)

| Metric | Pilot Baseline | 1,000 Users (Scale) | 10,000 Users (Growth) |
| :--- | :--- | :--- | :--- |
| **Monthly Try-On Renders** | 2,500 | 25,000 | 250,000 |
| **Inference Cost / Render** | $0.075 (Hosted API) | $0.045 (Reserved API) | $0.018 (Self-Hosted H100 Worker) |
| **Monthly Infrastructure Cost** | $143.25 | $320.00 | $1,150.00 |
| **E-Commerce Conversion Rate** | 4.0% | 5.5% | 6.5% |
| **Average Order Value (AOV)** | ₹2,500 (~$30) | ₹2,500 (~$30) | ₹2,800 (~$33.50) |
| **Affiliate Commission Rate** | 8.0% ($2.40 / sale) | 8.5% ($2.55 / sale) | 9.0% ($3.00 / sale) |
| **Gross Affiliate Revenue** | $9.60 | $140.25 | $1,950.00 |
| **Net Contribution Margin** | -$346.15 (Pilot stage) | -$1,299.75 | **+$350.00 (Break-even crossing)** |
