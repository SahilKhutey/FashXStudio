import {
  isSafeRetailerRedirect,
  assertSafeRetailerRedirect,
} from "../safeRedirect";

describe("safeRedirect", () => {
  describe("isSafeRetailerRedirect", () => {
    it("accepts valid HTTPS URLs", () => {
      expect(isSafeRetailerRedirect("https://example.com/product/123")).toBe(true);
      expect(
        isSafeRetailerRedirect("https://shop.nordstrom.com/s/sample-dress?sku=456")
      ).toBe(true);
      expect(isSafeRetailerRedirect("https://store.brand.co.uk/item/789")).toBe(true);
    });

    it("rejects non-HTTPS protocols", () => {
      expect(isSafeRetailerRedirect("http://example.com/product")).toBe(false);
      expect(isSafeRetailerRedirect("javascript:alert(1)")).toBe(false);
      expect(isSafeRetailerRedirect("file:///etc/passwd")).toBe(false);
      expect(isSafeRetailerRedirect("data:text/html,<script>alert(1)</script>")).toBe(false);
      expect(isSafeRetailerRedirect("ftp://example.com/file")).toBe(false);
    });

    it("rejects empty or null inputs", () => {
      expect(isSafeRetailerRedirect(null)).toBe(false);
      expect(isSafeRetailerRedirect(undefined)).toBe(false);
      expect(isSafeRetailerRedirect("")).toBe(false);
      expect(isSafeRetailerRedirect("   ")).toBe(false);
    });

    it("rejects URLs with embedded credentials", () => {
      expect(isSafeRetailerRedirect("https://user:password@example.com/path")).toBe(false);
      expect(isSafeRetailerRedirect("https://admin@example.com/path")).toBe(false);
    });

    it("rejects invalid URL strings", () => {
      expect(isSafeRetailerRedirect("not-a-url")).toBe(false);
      expect(isSafeRetailerRedirect("https://")).toBe(false);
    });

    it("filters against allowedHosts when provided", () => {
      const allowed = ["nordstrom.com", "ssense.com", "zara.com"];

      expect(isSafeRetailerRedirect("https://nordstrom.com/item/1", allowed)).toBe(true);
      expect(isSafeRetailerRedirect("https://shop.nordstrom.com/item/1", allowed)).toBe(true);
      expect(isSafeRetailerRedirect("https://www.ssense.com/en-us/item", allowed)).toBe(true);

      expect(isSafeRetailerRedirect("https://evil.com/item/1", allowed)).toBe(false);
      expect(isSafeRetailerRedirect("https://fake-nordstrom.com/item/1", allowed)).toBe(false);
    });
  });

  describe("assertSafeRetailerRedirect", () => {
    it("returns trimmed URL when valid", () => {
      const url = "  https://example.com/item  ";
      expect(assertSafeRetailerRedirect(url)).toBe("https://example.com/item");
    });

    it("throws descriptive error when invalid", () => {
      expect(() => assertSafeRetailerRedirect("http://insecure.com")).toThrow(
        /Unsafe retailer redirect URL rejected/
      );
      expect(() => assertSafeRetailerRedirect(null)).toThrow(
        /Unsafe retailer redirect URL rejected/
      );
    });
  });
});
