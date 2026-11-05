# RC-06 — Shopping & Purchase Handoff Architecture

## System Architecture

The FashXStudio shopping architecture connects catalog acquisition, product discovery, multi-merchant offer aggregation, digital wardrobe persistence, and secure outbound retailer redirection.

```mermaid
flowchart TD
    subgraph Discovery ["1. Product Discovery"]
        Feed["Customer Feed / Search"] --> Garment["Canonical Garment Detail"]
        Garment --> Offers["Multi-Merchant Offers"]
    end

    subgraph Comparison ["2. Offer Comparison & Selection"]
        Offers --> Ranker["Offer Sorting Engine<br/>- In-Stock First<br/>- Price Ascending"]
        Ranker --> Selected["User Selects Explicit Offer"]
    end

    subgraph Commerce ["3. Purchase Handoff & Attribution"]
        Selected --> BuyClickAPI["POST /commerce/buy-clicks<br/>- Requires garment_id & offer_id<br/>- Validates active garment & in-stock<br/>- Resolves user from JWT principal"]
        BuyClickAPI --> URLValidator["validate_retailer_url<br/>- HTTPS Enforced<br/>- Credentials Rejected<br/>- Allowlist Domain Match"]
        URLValidator --> Attribution["Attach Attribution Params<br/>- utm_source=fashx<br/>- utm_medium=app<br/>- utm_campaign=vto_purchase<br/>- sub_id=user_id<br/>- click_id=buy_click_id"]
        Attribution --> ClickEvent["Record BuyClickEvent in DB"]
    end

    subgraph Handoff ["4. External Retailer Navigation"]
        ClickEvent --> MobileClient["Mobile App Expo Linking"]
        MobileClient --> RetailerStore["External Retailer Website<br/>(e.g., Myntra, Ajio, Tata CLiQ)"]
    end

    subgraph Wardrobe ["5. Parallel Wardrobe Action"]
        Garment --> SaveWardrobe["POST /wardrobe/items<br/>Snapshot Price & Title"]
        SaveWardrobe --> Closet["Digital Closet Persistence"]
    end
```

## Architectural Boundaries

1. **Catalog Domain (`fashx/catalog`)**:
   - Manages canonical fashion taxonomy, merchant products, and multi-merchant offers.
   - Provides customer-facing garment detail resolution with calculated best in-stock price and merchant name lookup.

2. **Commerce & Wardrobe Domain (`fashx/commerce_wardrobe`)**:
   - Manages buy-click attribution lifecycle and outbound link generation.
   - Houses user wardrobe items with immutable pricing and title snapshots at the moment of addition.

3. **Security & Identity Gateway (`fashx/security`)**:
   - Authenticates mobile client requests via JWT.
   - Extracts principal subject and guarantees caller identity cannot be spoofed across users.

4. **Mobile Client (`mobile/`)**:
   - React Native Expo application with React Query and TypeScript.
   - Provides interactive radio selection for retailer offers, displaying currency formatting and stock status.
