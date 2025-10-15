import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { url, format = "png" } = await request.json()

    if (!url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 })
    }

    // Validate URL
    try {
      new URL(url)
    } catch {
      return NextResponse.json({ error: "Invalid URL format" }, { status: 400 })
    }

    console.log("Starting Puppeteer screenshot for:", url)

    // Import Puppeteer dynamically
    const puppeteer = await import("puppeteer")
    console.log("Puppeteer imported successfully")

    // Launch browser with minimal configuration
    const browser = await puppeteer.default.launch({
      headless: "new",
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
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    console.log("User agent set")

    // Navigate to URL
    await page.goto(url, { waitUntil: "load", timeout: 30000 })
    console.log("Page loaded")

    // Wait for dynamic content
    await new Promise((resolve) => setTimeout(resolve, 2000))
    console.log("Wait completed")

    // Take screenshot
    const screenshot = await page.screenshot({
      type: format === "jpg" ? "jpeg" : "png",
      fullPage: true,
      quality: format === "jpg" ? 90 : undefined,
    })
    console.log("Screenshot taken, size:", screenshot.length)

    await browser.close()
    console.log("Browser closed")

    // Return screenshot
    const contentType = format === "jpg" ? "image/jpeg" : "image/png"
    const fileExtension = format === "jpg" ? "jpg" : "png"

    return new NextResponse(screenshot, {
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": `attachment; filename="screenshot-${Date.now()}.${fileExtension}"`,
      },
    })
  } catch (error) {
    console.error("Screenshot API error:", error)
    return NextResponse.json(
      { error: `Failed to capture screenshot: ${error.message}` },
      { status: 500 }
    )
  }
}
