import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { url, action, selector, text, x, y } = await request.json()

    if (!url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 })
    }

    // Validate URL
    try {
      new URL(url)
    } catch {
      return NextResponse.json({ error: "Invalid URL format" }, { status: 400 })
    }

    console.log("Starting interactive browser session for:", url)

    // Import Puppeteer dynamically
    const puppeteer = await import("puppeteer")
    console.log("Puppeteer imported successfully")

    // Launch browser with full functionality
    const browser = await puppeteer.default.launch({
      headless: false, // We want to see the browser
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

    let result = null

    // Handle different actions
    if (action === "click" && selector) {
      console.log("Clicking element:", selector)
      await page.click(selector)
      await new Promise((resolve) => setTimeout(resolve, 2000))
      result = { action: "click", selector, success: true }
    } else if (action === "type" && selector && text) {
      console.log("Typing text:", text, "into:", selector)
      await page.type(selector, text)
      result = { action: "type", selector, text, success: true }
    } else if (action === "screenshot") {
      console.log("Taking screenshot")
      const screenshot = await page.screenshot({
        type: "png",
        fullPage: true,
      })
      result = { action: "screenshot", data: screenshot.toString("base64") }
    } else if (action === "get_html") {
      console.log("Getting page HTML")
      const html = await page.content()
      result = { action: "get_html", html }
    } else {
      // Default: just get the current state
      console.log("Getting page state")
      const html = await page.content()
      const screenshot = await page.screenshot({
        type: "png",
        fullPage: true,
      })
      result = {
        action: "get_state",
        html,
        screenshot: screenshot.toString("base64"),
        url: page.url(),
      }
    }

    // Don't close browser immediately - keep it open for interaction
    // await browser.close()
    console.log("Action completed")

    return NextResponse.json({
      success: true,
      result,
      browserId: `browser_${Date.now()}`, // In a real implementation, you'd store this
    })
  } catch (error) {
    console.error("Interactive browser error:", error)
    return NextResponse.json(
      {
        error: `Failed to interact with browser: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      },
      { status: 500 }
    )
  }
}
