const fs = require("fs");
const path = require("path");

describe("AI Interview & GD Practice - index.html", () => {

    const filePath = path.join(__dirname, "index.html");
    let html;

    beforeAll(() => {
        html = fs.readFileSync(filePath, "utf8");
    });

    test("index.html should exist", () => {
        expect(fs.existsSync(filePath)).toBe(true);
    });

    test("should have correct HTML doctype", () => {
        expect(html.toLowerCase()).toContain("<!doctype html>");
    });

    test("should have viewport meta tag", () => {
        expect(html).toContain('name="viewport"');
        expect(html).toContain("width=device-width");
    });

    test("should have correct title", () => {
        expect(html).toContain("<title>AI Interview & GD Practice</title>");
    });

    test("should have React root element", () => {
        expect(html).toContain('<div id="root"></div>');
    });

    test("should include JavaScript asset", () => {
        expect(html).toMatch(
            /<script[^>]+type="module"[^>]+src="\/assets\/index-[^"]+\.js"/
        );
    });

    test("should include CSS asset", () => {
        expect(html).toMatch(
            /<link[^>]+rel="stylesheet"[^>]+href="\/assets\/index-[^"]+\.css"/
        );
    });

});
