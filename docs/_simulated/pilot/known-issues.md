# Pilot Known Issues & Workarounds

**Status**: Actively updated during closed pilot  
**Current Pilot Build**: `v0.9.1-pilot`  

---

| Issue ID | Affected Screen | Description | Temporary Workaround | Status / Planned Fix |
| :--- | :--- | :--- | :--- | :--- |
| **KI-01** | Photo Upload | Mirror selfies where phone blocks the chest occasionally fail silhouette extraction with `BLURRY` or `CROPPED_BODY`. | Place phone on a shelf or ask a friend to take a photo 6–8 feet away. | Adding live camera silhouette overlay guide in next build. |
| **KI-02** | Virtual Try-On | Loose draped garments (unstitched sarees, dupattas) show minor fabric edge softness around wrists. | Western wear (shirts, t-shirts, kurtas, dresses) renders with sharpest edges. | Fine-tuning edge segmentation weights in background. |
| **KI-03** | Feed Scroll | On older Android devices with <4GB RAM, rapid scrolling can cause brief image reload flicker. | Scroll at normal browsing speed; images cache automatically. | Released memory optimization patch in `v0.9.1`. |
| **KI-04** | Buy Redirect | Clicking "Buy on Store" on some Flipkart affiliate items opens mobile web browser instead of the Flipkart app. | Seamless purchase works on both mobile browser and app; login required on merchant page. | Updating deep link scheme handling. |
| **KI-05** | Closet | Saved items occasionally take 1–2 seconds to show up in Closet tab after tapping heart icon. | Pull down to refresh the Closet screen. | State synchronization patch deployed. |
