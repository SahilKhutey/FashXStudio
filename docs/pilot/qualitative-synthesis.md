# Closed Pilot Qualitative Synthesis (Phase 10)

**Data Inputs**: 10 semi-structured user interviews (including 2 participants who dropped out or ceased usage), 39 completed survey free-text submissions, and 24 in-app structured feedback messages.  
**Methodology**: All inputs were independently coded into 10 qualitative themes. In accordance with Section 10.19 of the pilot plan, metrics report the **number of unique participants** raising each theme (not message frequency), accompanied by anonymized verbatim quotes, perceived severity, and proposed technical/product mitigations.

---

## 1. Qualitative Themes & Coded Feedback

### Theme 1: Trust & Privacy (Raised by 31 participants)
- **Sentiment**: Strongly Positive / Reassured
- **Severity**: Low (Addressed by design)
- **Representative Quotes**:
  - *"I usually never upload body pictures to random AI apps because you never know where they end up. Seeing the explicit DPDP consent and knowing it doesn’t go to a public gallery made me comfortable."*
  - *"The fact that the app guided me to stand in front of a mirror and calibrated immediately gave me a sense of serious engineering rather than a gimmick."*
- **Candidate Fix**: Maintain the existing local-first, zero-retention guarantee; add explicit visual reassurance of photo deletion upon account closure.

### Theme 2: Try-On Realism & Visual Fidelity (Raised by 28 participants)
- **Sentiment**: High Praise / Surpassed Expectations
- **Severity**: Low
- **Representative Quotes**:
  - *"It actually showed how the kurta falls over my shoulders instead of just pasting a sticker over my chest. I could see the seam drape."*
  - *"The fabric texture in the close-up zoom looked like real linen, not synthetic plastic."*
- **Candidate Fix**: Continue fine-tuning hemline alignment on flared silhouettes (anarkalis, skirts).

### Theme 3: Fit Accuracy & Sizing Confidence (Raised by 22 participants)
- **Sentiment**: Constructive / Eager for More Nuance
- **Severity**: Medium
- **Representative Quotes**:
  - *"The visual fit looked true to my size, but I still hesitated because brand 'M' in Zara is often tighter than brand 'M' in FabIndia."*
  - *"Seeing it on my silhouette helped me realize that high-waisted trousers suit my torso much better than mid-rise."*
- **Candidate Fix**: Surface multi-brand size normalization charts with chest/waist measurements directly in the try-on result view.

### Theme 4: Selection & Catalog Diversity (Raised by 19 participants)
- **Sentiment**: Mixed (Praise for curation, desire for broader inventory)
- **Severity**: Medium
- **Representative Quotes**:
  - *"The ethnic wear selection was great, but I wished there were more formal office wear options in XL."*
  - *"I loved that everything I saw was actually in stock in my size—no clickbait out-of-stock items."*
- **Candidate Fix**: Expand merchant catalog ingestion pipeline to bring in 15k+ SKUs focusing on plus-size workwear.

### Theme 5: Price & Commercial Transparency (Raised by 16 participants)
- **Sentiment**: Neutral / Practical
- **Severity**: Low
- **Representative Quotes**:
  - *"The price badge on the card was accurate when I clicked through to Myntra. No hidden affiliate markup."*
  - *"Would be awesome if it alerted me when a saved try-on item goes on discount."*
- **Candidate Fix**: Implement background price-drop notifications on Closet items for Phase 11.

### Theme 6: Latency & Speed (Raised by 15 participants)
- **Sentiment**: Positive
- **Severity**: Low
- **Representative Quotes**:
  - *"Under ten seconds for a full outfit render is fast enough that I didn't get bored waiting."*
  - *"The loading animation showing styling steps kept me entertained while the image generated."*
- **Candidate Fix**: Maintain asynchronous Redis task architecture and GPU warm pools.

### Theme 7: Onboarding Friction (Raised by 11 participants)
- **Sentiment**: Friction Points Identified
- **Severity**: Medium
- **Representative Quotes**:
  - *"I tried taking a photo in my bedroom in the evening, and it kept telling me the lighting was insufficient. I had to wait until morning for natural light."*
  - *"The quiz was quick, but I wasn't sure if 'Smart Casual' meant collar shirts or polo t-shirts."*
- **Candidate Fix**: Add on-screen ambient lighting exposure indicator and photo retake shortcut during onboarding.

### Theme 8: Software Bugs & Polish (Raised by 8 participants)
- **Sentiment**: Minor Annoyances (Rapidly resolved)
- **Severity**: Low
- **Representative Quotes**:
  - *"On Day 2, tapping Save didn't vibrate on my OnePlus phone, so I tapped it three times."*
  - *"The image dissolve comparison flickered slightly on iOS battery saver mode."*
- **Candidate Fix**: Fixed via OTA release v0.10.1 (haptics and render optimizations).

### Theme 9: Missing Features & Roadmap Desires (Raised by 24 participants)
- **Sentiment**: High Engagement / Wishlist
- **Severity**: Informational
- **Representative Quotes**:
  - *"I want to be able to mix and match a top from one brand with a skirt from another brand in a single try-on."*
  - *"I'd love to share the generated image directly to Instagram Stories or WhatsApp with my stylist friend."*
- **Candidate Fix**: Plan Multi-Garment Outfit Stacking (F06) and 1-Click Social Sharing for Phase 11.

### Theme 10: User Delight & Discovery (Raised by 26 participants)
- **Sentiment**: Strong Delight
- **Severity**: Positive Driver
- **Representative Quotes**:
  - *"I ended up buying a teal kurta I never would have picked from a regular grid photo because on my skin tone it actually looked vibrant."*
  - *"This completely eliminates the anxiety of ordering online and returning 3 different sizes."*
- **Candidate Fix**: Leverage personalized color harmony as a soft visual indicator in feed discovery.

---

## 2. In-Depth Dropout & Attrition Analysis

To avoid survivorship bias, 2 qualitative interviews were conducted with participants who stopped engaging after their initial session:

### Dropout Case A (Wave 1 Participant, Inactive after Day 3)
- **Observed Behavior**: Completed onboarding, generated 1 try-on, never returned.
- **Interview Feedback**:
  - *"The app was slick, but I was in the middle of university semester examinations and had no mental bandwidth to shop for clothes. I also doubted whether the colors were true because my original photo had yellow incandescent lighting."*
- **Analysis**: Time pressure combined with self-doubt regarding photo calibration. Not an active rejection of product utility.

### Dropout Case B (Wave 2 Participant, Inactive after Day 2)
- **Observed Behavior**: Completed onboarding, browsed feed for 12 minutes, zero try-ons triggered.
- **Interview Feedback**:
  - *"I specifically wanted oversized streetwear blazers in XXL. The feed showed great kurtas and shirts, but only 2 blazers were available in my size. I felt the selection was too narrow for my specific niche aesthetic."*
- **Analysis**: Catalog depth bottleneck for specialized plus-size streetwear. Confirms that catalog variety directly dictates activation for niche shopper personas.

---

## 3. Discrepancy Analysis: Stated Intent vs. Empirical Behavior

| Dimension | What Participants Said (Qualitative Words) | What Participants Did (Empirical Telemetry) | Analytical Truth & Synthesis |
| :--- | :--- | :--- | :--- |
| **Willingness to Purchase** | 82% of survey respondents stated they *"definitely plan to purchase clothes discovered through the app"*. | Only **47.4%** clicked external merchant links, and **3 verified purchases** occurred. | **Words overestimate action**: Stated purchase intent carries novelty inflation. Real-world checkout requires alignment of immediate budget, seasonal need, and merchant shipping friction. |
| **Catalog Breadth** | 19 participants requested *"thousands more brands and items"*. | Participants spent a median of 18 minutes exploring fewer than 150 items, repeatedly trying on items from the same 3 top brands. | **Curation beats volume**: Users feel restricted when inventory appears small, but in practice, they concentrate attention on high-confidence, well-fitting staples. |
| **Privacy Apprehension** | Several users remarked in interviews that taking a body photo is *"inherently sensitive and intimidating"*. | **95.0%** of participants who started onboarding successfully completed photo capture, with **0%** abandoning at the consent stage. | **Trust is earned through transparency**: Upfront clarity and on-device pose overlay neutralize latent hesitation. |
| **Feature Complexity** | Users requested advanced features (outfit stacking, multi-item layering, social styling feeds). | The highest-retention users relied exclusively on the simple 2-step loop: Browse Feed ➔ Instant Try-On ➔ Save to Closet. | **Simplicity drives habit**: Advanced features must not compromise the instantaneous single-garment discovery loop. |
