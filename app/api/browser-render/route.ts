import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { url, action = "navigate" } = await request.json()

    if (!url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 })
    }

    // Validate URL
    try {
      new URL(url)
    } catch {
      return NextResponse.json({ error: "Invalid URL format" }, { status: 400 })
    }

    console.log("Starting browser session for:", url)

    // Import Puppeteer dynamically
    const puppeteer = await import("puppeteer")
    console.log("Puppeteer imported successfully")

    // Launch browser with full functionality
    const browser = await puppeteer.default.launch({
      headless: true, // Headless for server use
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--no-first-run",
        "--disable-default-apps",
        "--window-size=1280,720",
      ],
    })
    console.log("Browser launched")

    const page = await browser.newPage()
    console.log("Page created")

    // Set viewport
    await page.setViewport({ width: 1280, height: 720 })
    console.log("Viewport set")

    // Set user agent to avoid detection
    await page.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    console.log("User agent set")

    // Navigate to URL
    await page.goto(url, { waitUntil: "load", timeout: 30000 })
    console.log("Page loaded")

    // Wait for dynamic content
    await new Promise((resolve) => setTimeout(resolve, 3000))
    console.log("Wait completed")

    // Get the rendered HTML after JavaScript execution
    const html = await page.content()
    console.log("HTML content retrieved")

    // Take a screenshot
    const screenshot = await page.screenshot({
      type: "png",
      fullPage: true,
    })
    console.log("Screenshot taken")

    await browser.close()
    console.log("Browser closed")

    // Return both HTML and screenshot
    return NextResponse.json({
      success: true,
      html,
      screenshot: Buffer.from(screenshot).toString("base64"),
      url: page.url(),
    })
  } catch (error) {
    console.error("Browser session error:", error)
    return NextResponse.json(
      {
        error: `Failed to load page: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      },
      { status: 500 }
    )
  }
}
