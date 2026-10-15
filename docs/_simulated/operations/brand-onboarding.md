# Brand Partner Onboarding Playbook (15-Minute Integration)

- **Target Audience:** Brand Tech Leads, Ecommerce Operations Managers, Shopify Developers
- **Platform Compatibility:** Shopify (Theme App Extension / Custom App), WooCommerce, Magento 2, Custom Headless Next.js/React storefronts.

---

## 1. Onboarding Timeline & Checklist

Integration takes under 15 minutes with zero core codebase modification:

| Step | Time | Task | Owner | Verification |
|---|---|---|---|---|
| **1. Provisioning** | 2 min | Generate Merchant API Key in FashX Portal | FashX Team | Key hash created in `tenant_keys` |
| **2. DPA Sign-off** | 3 min | Sign standard DPDP Data Processing Agreement | Brand Counsel / CEO | Counter-signed PDF in Data Room |
| **3. Widget Embed** | 4 min | Add script tag or Theme App Extension to PDP | Store Developer | Button appears beside size selector |
| **4. Catalog Sync** | 4 min | Connect Shopify product feed webhook | Store Developer | Products visible in `/merchant/dashboard` |
| **5. Smoke Test** | 2 min | Perform test try-on and size addition to cart | Both teams | Session verified in analytics view |

---

## 2. Integration Code Snippet (Shopify PDP Embed)

### Option A: Shopify Theme App Extension (Recommended)
Add the FashXStudio Fit App Block directly in the Shopify Theme Customizer under the **Product Information** section.

### Option B: Direct Liquid Embed (`product.liquid` / `main-product.liquid`)
Paste this snippet immediately adjacent to the size variant selector buttons:

```liquid
<!-- FashXStudio AI Fit & Drape Widget (Encapsulated Shadow DOM) -->
<div class="fashx-widget-mount" style="margin: 12px 0;"></div>
<script
  src="https://cdn.fashxstudio.com/widget/fashx-widget.js"
  data-tenant-key="{{ shop.metafields.fashx.api_key }}"
  data-product-id="{{ product.id }}"
  data-product-category="{{ product.type | default: 'apparel' }}"
  async
></script>
<script>
  // Listen for Add to Bag events dispatched from FashXStudio Shadow DOM
  document.addEventListener('fashx:add-to-cart', function (e) {
    const { productId, recommendedSize } = e.detail;
    console.log('[BrandStore] Auto-selecting recommended size:', recommendedSize);
    
    // Auto-select size radio button on brand PDP
    const sizeInput = document.querySelector(`input[name="Size"][value="${recommendedSize}"]`);
    if (sizeInput) {
      sizeInput.click();
      sizeInput.checked = true;
    }
  });
</script>
```

---

## 3. Webhook Configuration for Return Tracking

To enable automated Difference-in-Differences return rate calculation:
1. Navigate to **Shopify Admin $\to$ Settings $\to$ Notifications $\to$ Webhooks**.
2. Create webhook:
   - **Event:** `Refunds create`
   - **Format:** `JSON`
   - **URL:** `https://api.fashxstudio.com/merchant/webhooks/refunds`
   - **Header:** Sent with shop HMAC for verification.
3. Repeat for `Orders fulfilled`.

---

## 4. Brand Go-Live Verification Gate

Before announcing live fit guidance to all store visitors:
- [ ] Test photo upload executed from iOS Safari and Android Chrome.
- [ ] Fit simulation response renders within $< 8$ seconds.
- [ ] Ephemeral 24h privacy notice visible to shoppers inside modal.
- [ ] Modal closes cleanly without interfering with native cart drawers.
- [ ] Test order placed and confirmed with `_fashx_recommended_size` cart property.
