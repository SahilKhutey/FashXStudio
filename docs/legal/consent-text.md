# Onboarding Consent Screen Copy & Multilingual Notice

**Statutory Standard**: DPDP Act 2023, Section 6 (Notice & Consent Architecture)  
**Languages Provided**: English (Primary) & Hindi (Summary Notice)  

---

## 1. Onboarding Screen 1: Camera & Photo Processing Notice

### English Text:
> ### Virtual Try-On Consent
> 
> To generate realistic previews of how clothes fit on your body, FashXStudio needs to process your self-portrait photo.
> 
> **Here is what we do with your photo:**
> - **Virtual Try-On Only**: Your photo is used exclusively to render clothing items onto your silhouette.
> - **Zero Foundation Model Training**: We **never** sell your photo or use it to train public AI models.
> - **Ephemeral Processing**: Unsaved try-ons automatically expire after 30 days. You can delete your photo and account anytime in Settings.
> - **Secure Storage**: Encrypted at rest in AWS Mumbai (`ap-south-1`).
> 
> *By tapping "I Agree & Continue", you provide free, specific, informed, and unconditional consent for FashXStudio to process your photo for virtual styling purposes in accordance with our Privacy Policy.*
> 
> `[Decline]` | `[I Agree & Continue]`

### Hindi Text (हिंदी अनुवाद):
> ### वर्चुअल ट्राई-ऑन सहमति
> 
> कपड़े आपके शरीर पर कैसे दिखते हैं, यह दिखाने के लिए FashXStudio को आपकी तस्वीर प्रोसेस करने की आवश्यकता है।
> 
> **आपकी तस्वीर के साथ हमारी प्रतिबद्धता:**
> - **केवल ट्राई-ऑन हेतु**: आपकी तस्वीर का उपयोग केवल कपड़ों का पूर्वावलोकन दिखाने के लिए किया जाता है।
> - **सार्वजनिक AI ट्रेनिंग नहीं**: हम आपकी तस्वीर किसी को नहीं बेचते और न ही इसे सार्वजनिक AI मॉडलों को ट्रेन करने के लिए उपयोग करते हैं।
> - **स्थायी नियंत्रण**: जो कपड़े आप सेव नहीं करते, वे 30 दिनों बाद अपने आप मिट जाते हैं। आप सेटिंग्स में जाकर कभी भी अपना डेटा मिटा सकते हैं।
> - **सुरक्षित भंडारण**: सारा डेटा भारत (AWS मुंबई) में सुरक्षित रूप से स्टोर होता है।
> 
> `[अस्वीकार करें]` | `[मैं सहमत हूँ और आगे बढ़ें]`

---

## 2. Onboarding Screen 2: 18+ Age & Terms Acknowledgment

### English Text:
> ### Confirm Age & Terms
> 
> FashXStudio is designed for adults aged 18 and older.
> 
> `[✓] I certify that I am 18 years of age or older.`  
> `[✓] I accept the Terms of Use, Privacy Policy, and Pilot Agreement.`  
> 
> `[Continue]`

---

## 3. Storage of Consent Record (Database Proof)

Every consent decision is immutably recorded in `consent_records`:
- `user_id`: UUID
- `data_type`: `"body_photo"` / `"style_preferences"`
- `granted`: `TRUE`
- `granted_at`: UTC timestamp
- `policy_version`: `"v0.9-pilot"`
- `ip_address`: Pseudonymized SHA-256 hash
