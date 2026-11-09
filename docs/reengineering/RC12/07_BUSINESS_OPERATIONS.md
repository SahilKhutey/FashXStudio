# RC12: Business Operations & Partner Integration

## 1. Merchant Handoff Model
FashXStudio operates on an affiliate/partner redirection model. In-app checkout, payments, and order fulfillment remain strictly out of scope.

## 2. Event Disambiguation Standards
Reports must separate commercial conversion stages:

| Term | Technical Event | Meaning |
| :--- | :--- | :--- |
| **Product View** | `garment_opened` | User viewed garment detail screen |
| **Retailer Click** | `retailer_opened` | User tapped "Buy on Store" |
| **Redirect Success** | Web browser opened | Destination merchant URL rendered |
| **Reported Purchase** | In-app feedback | User self-reported buying the item |
| **Verified Purchase** | Partner conversion API | Merchant settlement confirms transaction |
| **Commission Earned** | Monthly statement | Audited partner invoice / payout |

*Click counts must never be reported as purchases or GMV.*
