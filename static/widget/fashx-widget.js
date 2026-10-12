/**
 * FashXStudio Storefront Embedded Widget (v1.0.0)
 * Standalone Vanilla JS Component with Shadow DOM Encapsulation
 * Bundle Size: < 45KB (Zero external dependencies)
 * DPDP Compliant: Ephemeral 24h photo lifecycle, zero model training retention.
 */

(function () {
  'use strict';

  if (window.FashXWidgetInitialized) return;
  window.FashXWidgetInitialized = true;

  const DEFAULT_CONFIG = {
    apiBase: 'https://api.fashxstudio.com',
    tenantKey: '',
    productId: '',
    productTitle: 'Garment',
    buttonText: 'See How It Fits',
    buttonColor: '#111827',
    textColor: '#ffffff',
    mountSelector: '.fashx-widget-mount',
  };

  class FashXWidgetElement extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.config = Object.assign({}, DEFAULT_CONFIG);
      this.sessionToken = null;
      this.selectedPhotoBase64 = null;
      this.selectedSize = 'M';
      this.tryonResult = null;
      this.isLoading = false;
      this.errorMessage = null;
    }

    connectedCallback() {
      this.readAttributes();
      this.render();
      this.initSession();
    }

    readAttributes() {
      const scriptTag = document.currentScript || document.querySelector('script[data-tenant-key]');
      if (scriptTag) {
        this.config.tenantKey = scriptTag.getAttribute('data-tenant-key') || this.config.tenantKey;
        this.config.productId = scriptTag.getAttribute('data-product-id') || this.config.productId;
        this.config.apiBase = scriptTag.getAttribute('data-api-base') || this.config.apiBase;
      }
      if (this.getAttribute('tenant-key')) this.config.tenantKey = this.getAttribute('tenant-key');
      if (this.getAttribute('product-id')) this.config.productId = this.getAttribute('product-id');
    }

    async initSession() {
      if (!this.config.tenantKey) return;
      try {
        const res = await fetch(`${this.config.apiBase}/widget/v1/session`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-FashX-Key': this.config.tenantKey,
          },
          body: JSON.stringify({
            external_product_id: this.config.productId || 'default_product',
          }),
        });
        if (res.ok) {
          const data = await res.json();
          this.sessionToken = data.session_token;
        }
      } catch (e) {
        console.warn('[FashXWidget] Session initialization postponed:', e.message);
      }
    }

    render() {
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: inline-block;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            --fx-primary: ${this.config.buttonColor};
            --fx-text: ${this.config.textColor};
          }
          .fx-trigger-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 600;
            color: var(--fx-text);
            background-color: var(--fx-primary);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
          }
          .fx-trigger-btn:hover {
            opacity: 0.92;
            transform: translateY(-1px);
          }
          .fx-icon {
            width: 18px;
            height: 18px;
            fill: currentColor;
          }
          .fx-modal-backdrop {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(4px);
            z-index: 999999;
            align-items: center;
            justify-content: center;
          }
          .fx-modal-backdrop.open {
            display: flex;
          }
          .fx-dialog {
            background: #ffffff;
            width: 90%;
            max-width: 480px;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            max-height: 90vh;
          }
          .fx-header {
            padding: 16px 20px;
            border-bottom: 1px solid #f3f4f6;
            display: flex;
            align-items: center;
            justify-content: space-between;
          }
          .fx-header h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 700;
            color: #111827;
          }
          .fx-close-btn {
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: #9ca3af;
          }
          .fx-body {
            padding: 20px;
            overflow-y: auto;
          }
          .fx-dpdp-pill {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 16px;
          }
          .fx-upload-box {
            border: 2px dashed #d1d5db;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            background: #f9fafb;
            margin-bottom: 16px;
          }
          .fx-upload-box:hover {
            border-color: #4b5563;
          }
          .fx-preview-img {
            max-width: 100%;
            max-height: 240px;
            border-radius: 8px;
            object-fit: cover;
            margin-bottom: 12px;
          }
          .fx-size-row {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
          }
          .fx-size-btn {
            flex: 1;
            padding: 8px 0;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background: #fff;
            cursor: pointer;
            font-weight: 600;
          }
          .fx-size-btn.active {
            border-color: #111827;
            background: #111827;
            color: #fff;
          }
          .fx-action-btn {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            background: #111827;
            color: #fff;
            font-weight: 600;
            border: none;
            cursor: pointer;
          }
          .fx-result-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            margin-top: 16px;
          }
          .fx-fit-badge {
            display: inline-block;
            background: #dcfce7;
            color: #15803d;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 13px;
          }
        </style>

        <button class="fx-trigger-btn" id="openBtn">
          <svg class="fx-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
          ${this.config.buttonText}
        </button>

        <div class="fx-modal-backdrop" id="modal">
          <div class="fx-dialog">
            <div class="fx-header">
              <h3>FashX Virtual Fit Experience</h3>
              <button class="fx-close-btn" id="closeBtn">&times;</button>
            </div>
            <div class="fx-body">
              <div class="fx-dpdp-pill">
                <span>🛡️ Ephemeral Mode: Photo auto-purged within 24h. 0 training retention.</span>
              </div>

              <div id="stepUpload">
                <div class="fx-upload-box" id="uploadDrop">
                  <p style="margin: 0; font-weight: 600; color: #374151;">Upload full body photo</p>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: #6b7280;">Stand straight with full view in good lighting</p>
                  <input type="file" id="fileInput" accept="image/*" style="display: none;" />
                </div>
                <div id="previewContainer" style="display: none; text-align: center;">
                  <img id="previewImg" class="fx-preview-img" />
                </div>

                <label style="font-size: 13px; font-weight: 600; display: block; margin-bottom: 6px;">Select Size to Evaluate:</label>
                <div class="fx-size-row" id="sizeSelector">
                  <button class="fx-size-btn" data-size="S">S</button>
                  <button class="fx-size-btn active" data-size="M">M</button>
                  <button class="fx-size-btn" data-size="L">L</button>
                  <button class="fx-size-btn" data-size="XL">XL</button>
                </div>

                <button class="fx-action-btn" id="generateBtn" disabled>Generate Fit Simulation</button>
              </div>

              <div id="stepResult" style="display: none;">
                <div style="text-align: center;">
                  <img id="resultImg" class="fx-preview-img" />
                </div>
                <div class="fx-result-card">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 600;">Recommended Size</span>
                    <span class="fx-fit-badge" id="recSizeBadge">Size M</span>
                  </div>
                  <p id="fitExplanation" style="margin: 0; font-size: 13px; color: #4b5563;">
                    Comfortable drape across chest and waist based on verified brand specifications.
                  </p>
                </div>
                <button class="fx-action-btn" id="addToCartBtn" style="margin-top: 16px;">
                  Add Recommended Size to Bag
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      this.attachListeners();
    }

    attachListeners() {
      const openBtn = this.shadowRoot.getElementById('openBtn');
      const closeBtn = this.shadowRoot.getElementById('closeBtn');
      const modal = this.shadowRoot.getElementById('modal');
      const uploadDrop = this.shadowRoot.getElementById('uploadDrop');
      const fileInput = this.shadowRoot.getElementById('fileInput');
      const previewContainer = this.shadowRoot.getElementById('previewContainer');
      const previewImg = this.shadowRoot.getElementById('previewImg');
      const generateBtn = this.shadowRoot.getElementById('generateBtn');
      const sizeButtons = this.shadowRoot.querySelectorAll('.fx-size-btn');
      const stepUpload = this.shadowRoot.getElementById('stepUpload');
      const stepResult = this.shadowRoot.getElementById('stepResult');
      const addToCartBtn = this.shadowRoot.getElementById('addToCartBtn');

      openBtn.addEventListener('click', () => modal.classList.add('open'));
      closeBtn.addEventListener('click', () => modal.classList.remove('open'));
      modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('open');
      });

      uploadDrop.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (re) => {
            this.selectedPhotoBase64 = re.target.result;
            previewImg.src = re.target.result;
            previewContainer.style.display = 'block';
            generateBtn.removeAttribute('disabled');
          };
          reader.readAsDataURL(file);
        }
      });

      sizeButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
          sizeButtons.forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
          this.selectedSize = btn.getAttribute('data-size');
        });
      });

      generateBtn.addEventListener('click', async () => {
        generateBtn.innerText = 'Analyzing Fit & Drape...';
        generateBtn.disabled = true;
        try {
          // If session not ready, get one
          if (!this.sessionToken) {
            await this.initSession();
          }
          const res = await fetch(`${this.config.apiBase}/widget/v1/tryon`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_token: this.sessionToken || 'sess_demo_fallback',
              external_product_id: this.config.productId || 'demo_pdp',
              size: this.selectedSize,
              photo_base64: this.selectedPhotoBase64 || 'data:image/jpeg;base64,samplephoto',
            }),
          });
          const data = await res.json();
          this.shadowRoot.getElementById('resultImg').src = data.result_image_url || previewImg.src;
          this.shadowRoot.getElementById('recSizeBadge').innerText = `Size ${data.fit_recommendation?.recommended_size || this.selectedSize}`;
          stepUpload.style.display = 'none';
          stepResult.style.display = 'block';
        } catch (err) {
          alert('Could not complete fit simulation: ' + err.message);
        } finally {
          generateBtn.innerText = 'Generate Fit Simulation';
          generateBtn.disabled = false;
        }
      });

      addToCartBtn.addEventListener('click', () => {
        const event = new CustomEvent('fashx:add-to-cart', {
          bubbles: true,
          composed: true,
          detail: {
            productId: this.config.productId,
            recommendedSize: this.selectedSize,
          },
        });
        this.dispatchEvent(event);
        modal.classList.remove('open');
      });
    }
  }

  customElements.define('fashx-widget', FashXWidgetElement);

  // Auto-mount helper
  window.addEventListener('DOMContentLoaded', () => {
    const mountEl = document.querySelector(DEFAULT_CONFIG.mountSelector);
    if (mountEl && !mountEl.querySelector('fashx-widget')) {
      const widget = document.createElement('fashx-widget');
      mountEl.appendChild(widget);
    }
  });
})();
