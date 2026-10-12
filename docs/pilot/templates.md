# Pilot Communication Message Templates

**Program**: FashXStudio Closed Beta / Pilot (October - November 2026)  
**Tone**: Respectful, clear, transparent, concise.  

---

## 1. Invitation Email / Direct Message

**Subject**: You're invited to the FashXStudio Closed Pilot 👗✨

> Hi {{First_Name}},
> 
> We are building FashXStudio — an AI-powered styling app designed to help you visualize real, buyable clothes on your own body silhouette before purchasing.
> 
> As someone whose eye for fashion we value, we’d love to invite you to our private closed pilot of 40–50 testers across India.
> 
> **What to expect:**
> - Test the app on your phone (Android or iPhone) over the next 2–3 weeks.
> - Upload a photo to see realistic virtual try-ons of curated partner garments.
> - Your photos are completely private: encrypted in AWS Mumbai, used exclusively for your try-ons, and **never** used to train public AI models. You can permanently delete your photos and account anytime with 1 tap.
> 
> **How to join:**
> 1. Download the pilot build using the instructions below.
> 2. When prompted on first launch, enter your unique single-use invite code:  
>    👉 **`{{INVITE_CODE}}`**
> 
> Thank you for helping us shape the future of personal styling!  
> — Sahil & The FashX Team

---

## 2. Install Instructions

### Android (Google Play Internal Testing):
> 1. Open this link from your Android phone: `https://play.google.com/apps/internaltest/{{APP_ID}}`
> 2. Ensure you are signed in with the Gmail address you provided: `{{TESTER_EMAIL}}`.
> 3. Accept the invite and tap **Download on Google Play**.
> 4. Open the app, enter your email for sign-in OTP, and enter your invite code.

### iOS (Apple TestFlight):
> 1. Install **TestFlight** from the App Store on your iPhone.
> 2. Open your TestFlight invitation email or click this redeem link: `https://testflight.apple.com/join/{{INVITE_TOKEN}}`.
> 3. Tap **Accept** and then **Install**.
> 4. Open the app, sign in with your email OTP, and enter your invite code.

---

## 3. Day-2 Check-in / Nudge

> Hi {{First_Name}},  
> 
> Hope you're settling into the FashX app!  
> 
> Have you had a chance to try on your first outfit yet? A quick tip: for the best silhouette accuracy, snap a full-body photo against plain lighting.  
> 
> If anything feels confusing or if you run into any glitch, tap the **"Report a Problem"** button in Settings or reply directly to this message. We read and reply to every note within 24 hours!

---

## 4. Weekly Update / "What We Fixed" Nudge

> Hi Pilot Team!  
> 
> Thank you for an amazing Week {{N}} of testing. Thanks to your feedback, we've just deployed an update that addresses several top issues you flagged:
> - Improved try-on garment edge rendering on ethnic wear kurtas.
> - Faster feed loading on 4G networks.
> - Fixed a layout glitch on Android devices with small screens.
> 
> Update your app in TestFlight / Google Play to see the improvements. We have a brief 2-minute survey waiting for you in the app after your next try-on!

---

## 5. End-of-Pilot Evaluation Request

> Hi {{First_Name}},  
> 
> As our closed pilot reaches its final week, we need your honest, unfiltered thoughts.  
> 
> We’ve opened our **Final Pilot Survey** in the app. It takes roughly 4–5 minutes and covers your experience with try-on realism, feed relevance, and overall usability.  
> 
> Open FashX and look for the survey prompt on your home screen, or tap **Settings > Final Survey**.  
> 
> As a small token of gratitude for completing the survey, we’ll send across your promised thank-you voucher!

---

## 6. Pilot Closure & Data Choices Notice

> Hi {{First_Name}},  
> 
> Our closed pilot has officially concluded. We cannot thank you enough for your time, candid feedback, and support over the past month.  
> 
> **What happens to your data next:**  
> In line with our strict privacy commitment, you have complete control over your account:  
> 1. **Delete Everything Now**: Reply "Delete" to this message, or tap **Settings > Delete Account** in the app. We will wipe your photos, profile, and try-ons permanently within 24 hours.  
> 2. **Keep Your Account**: Keep your account active to retain access to future pilot updates and your saved closet items.  
> 
> Unsaved try-on images older than 30 days are automatically purged from our cloud storage.  
> 
> Thank you again for being an essential part of our early journey!
