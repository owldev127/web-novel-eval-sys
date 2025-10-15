import { NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const url = searchParams.get("url")

    if (!url) {
      return NextResponse.json(
        { error: "URL parameter is required" },
        { status: 400 }
      )
    }

    // Validate URL
    try {
      new URL(url)
    } catch {
      return NextResponse.json({ error: "Invalid URL format" }, { status: 400 })
    }

    console.log("Fetching content for:", url)

    // Fetch the website content with enhanced headers
    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        Accept:
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua":
          '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    let html = await response.text()

    // Remove restrictive headers and policies
    html = html.replace(
      /<meta[^>]*http-equiv=["']X-Frame-Options["'][^>]*>/gi,
      ""
    )
    html = html.replace(
      /<meta[^>]*http-equiv=["']Content-Security-Policy["'][^>]*>/gi,
      ""
    )

    // Remove any existing CSP headers
    html = html.replace(
      /<meta[^>]*content=["'][^"']*frame-ancestors[^"']*["'][^>]*>/gi,
      ""
    )

    // Add permissive meta tags and styles
    html = html.replace(
      "<head>",
      `<head>
        <meta http-equiv="X-Frame-Options" content="ALLOWALL">
        <meta http-equiv="Content-Security-Policy" content="frame-ancestors *; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline'; img-src * data: blob:; connect-src *; font-src *; object-src *; media-src *; child-src *; frame-src *; worker-src *; manifest-src *; form-action *; base-uri *;">
        <style>
          body { margin: 0; padding: 0; }
          html, body { height: 100%; overflow-x: auto; }
          /* Fix for Amazon's layout in iframe */
          #dp-container { min-height: 100vh; }
        </style>`
    )

    // Convert relative URLs to absolute URLs
    const baseUrl = new URL(url)
    html = html.replace(
      /(src|href)=["']([^"']+)["']/g,
      (match, attr, value) => {
        if (
          value.startsWith("http://") ||
          value.startsWith("https://") ||
          value.startsWith("//")
        ) {
          return match
        }
        if (value.startsWith("/")) {
          return `${attr}="${baseUrl.origin}${value}"`
        }
        return `${attr}="${baseUrl.origin}/${value}"`
      }
    )

    return new NextResponse(html, {
      headers: {
        "Content-Type": "text/html",
        "X-Frame-Options": "ALLOWALL",
        "Content-Security-Policy": "frame-ancestors *;",
      },
    })
  } catch (error) {
    console.error("Proxy error:", error)
    return NextResponse.json(
      {
        error: `Failed to fetch website: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      },
      { status: 500 }
    )
  }
}
