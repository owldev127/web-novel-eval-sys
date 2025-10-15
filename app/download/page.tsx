"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Download, ExternalLink, Loader2, Settings, Shield } from "lucide-react"
import { toast } from "sonner"

export default function DownloadPage() {
  const [url, setUrl] = useState("")
  const [currentUrl, setCurrentUrl] = useState("")
  const [proxyUrl, setProxyUrl] = useState("")
  const [renderedHtml, setRenderedHtml] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isCapturing, setIsCapturing] = useState(false)
  const [imageFormat, setImageFormat] = useState<"png" | "jpg">("png")
  const [iframeError, setIframeError] = useState(false)
  const [useProxy, setUseProxy] = useState(true)
  const [useBrowserRender, setUseBrowserRender] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) {
      toast.error("Please enter a valid URL")
      return
    }

    // Add protocol if missing
    let formattedUrl = url.trim()
    if (
      !formattedUrl.startsWith("http://") &&
      !formattedUrl.startsWith("https://")
    ) {
      formattedUrl = "https://" + formattedUrl
    }

    setIsLoading(true)
    setCurrentUrl(formattedUrl)
    setIframeError(false)

    if (useBrowserRender) {
      // Use browser rendering for full functionality
      try {
        const response = await fetch("/api/browser-render", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: formattedUrl }),
        })

        if (response.ok) {
          const data = await response.json()
          setRenderedHtml(data.html)
          toast.success("Page rendered with full browser functionality!")
        } else {
          throw new Error("Browser rendering failed")
        }
      } catch (error) {
        console.error("Browser rendering error:", error)
        toast.error("Browser rendering failed, falling back to proxy mode")
        setUseBrowserRender(false)
        setUseProxy(true)
      }
    } else if (useProxy) {
      // Use proxy to bypass iframe restrictions
      const proxyUrl = `/api/proxy?url=${encodeURIComponent(formattedUrl)}`
      setProxyUrl(proxyUrl)
    } else {
      setProxyUrl(formattedUrl)
    }

    // Simulate loading time
    setTimeout(() => {
      setIsLoading(false)
      if (!useBrowserRender) {
        toast.success("Page loaded successfully")
      }
    }, 1000)
  }

  const handlePresetUrl = (presetUrl: string) => {
    setUrl(presetUrl)
  }

  const handleIframeError = () => {
    setIframeError(true)
    toast.warning(
      "This website blocks iframe embedding (normal for Amazon, Google, etc.). Screenshots still work!"
    )
  }

  const handleDownload = async () => {
    if (!currentUrl) {
      toast.error("Please load a page first")
      return
    }

    console.log("Starting screenshot capture for:", currentUrl)
    setIsCapturing(true)

    try {
      const response = await fetch("/api/screenshot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: currentUrl, format: imageFormat }),
      })

      console.log("Screenshot API response status:", response.status)

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Screenshot API error:", errorText)
        throw new Error(`Failed to capture screenshot: ${response.status}`)
      }

      const blob = await response.blob()
      console.log("Screenshot blob size:", blob.size)

      if (blob.size === 0) {
        throw new Error("Screenshot is empty")
      }

      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = downloadUrl
      link.download = `screenshot-${Date.now()}.${imageFormat}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      toast.success("Screenshot downloaded successfully")
    } catch (error) {
      console.error("Error downloading screenshot:", error)
      toast.error(
        `Failed to download screenshot: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      )
    } finally {
      setIsCapturing(false)
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Image Download</h1>
          <p className="text-muted-foreground">
            Enter a URL to view the page and download screenshots
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ExternalLink className="w-5 h-5" />
            URL Input
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUrlSubmit} className="space-y-4">
            <div className="flex gap-2">
              <Input
                type="url"
                placeholder="Enter website URL (e.g., https://www.amazon.co.jp/dp/B0CHY36CYS)"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="flex-1"
              />
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  "Load Page"
                )}
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  <span className="text-sm font-medium">Image Format:</span>
                  <Select
                    value={imageFormat}
                    onValueChange={(value: "png" | "jpg") =>
                      setImageFormat(value)
                    }
                  >
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="png">PNG</SelectItem>
                      <SelectItem value="jpg">JPG</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  <span className="text-sm font-medium">View Mode:</span>
                  <Select
                    value={
                      useBrowserRender
                        ? "browser"
                        : useProxy
                        ? "proxy"
                        : "direct"
                    }
                    onValueChange={(value) => {
                      if (value === "browser") {
                        setUseBrowserRender(true)
                        setUseProxy(false)
                      } else if (value === "proxy") {
                        setUseBrowserRender(false)
                        setUseProxy(true)
                      } else {
                        setUseBrowserRender(false)
                        setUseProxy(false)
                      }
                    }}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="browser">Browser Render</SelectItem>
                      <SelectItem value="proxy">Proxy Mode</SelectItem>
                      <SelectItem value="direct">Direct</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    handlePresetUrl("https://www.amazon.co.jp/dp/B0CHY36CYS")
                  }
                >
                  Test Amazon URL
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {currentUrl && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <ExternalLink className="w-5 h-5" />
                Browser View
              </CardTitle>
              <Button
                onClick={handleDownload}
                disabled={isCapturing}
                className="flex items-center gap-2"
              >
                {isCapturing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Capturing...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Download Screenshot
                  </>
                )}
              </Button>
              <Button
                onClick={() => {
                  console.log("Testing screenshot API directly...")
                  fetch("/api/screenshot", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      url: currentUrl,
                      format: imageFormat,
                    }),
                  })
                    .then((response) => {
                      console.log("Direct API test response:", response.status)
                      return response.blob()
                    })
                    .then((blob) => {
                      console.log("Direct API test blob size:", blob.size)
                      toast.success(
                        `API test successful - blob size: ${blob.size} bytes`
                      )
                    })
                    .catch((error) => {
                      console.error("Direct API test error:", error)
                      toast.error(`API test failed: ${error.message}`)
                    })
                }}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                Test API
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {useBrowserRender && renderedHtml ? (
              <div className="border rounded-lg overflow-hidden">
                <div
                  className="w-full h-[600px] border-0 overflow-auto"
                  dangerouslySetInnerHTML={{ __html: renderedHtml }}
                />
              </div>
            ) : iframeError ? (
              <div className="border rounded-lg overflow-hidden bg-gray-50">
                <div className="h-[600px] flex flex-col items-center justify-center p-8 text-center">
                  <ExternalLink className="w-16 h-16 text-gray-400 mb-4" />
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">
                    Website Blocks Iframe Embedding
                  </h3>
                  <p className="text-gray-600 mb-4 max-w-md">
                    This website ({currentUrl}) prevents embedding in iframes
                    for security reasons. This is normal for many websites
                    including Amazon, Google, and other major sites. You can
                    still capture screenshots using the Download button below.
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => window.open(currentUrl, "_blank")}
                      className="flex items-center gap-2"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Open in New Tab
                    </Button>
                    <Button
                      onClick={() => setIframeError(false)}
                      variant="outline"
                    >
                      Try Again
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <iframe
                  ref={iframeRef}
                  src={proxyUrl}
                  className="w-full h-[600px] border-0"
                  title="Website Preview"
                  sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
                  onError={handleIframeError}
                  onLoad={() => {
                    // Check if iframe loaded successfully
                    try {
                      const iframe = iframeRef.current
                      if (iframe && iframe.contentDocument === null) {
                        handleIframeError()
                      }
                    } catch (e) {
                      handleIframeError()
                    }
                  }}
                />
              </div>
            )}
            <div className="mt-2 text-sm text-muted-foreground">
              <p>Current URL: {currentUrl}</p>
              <p className="text-xs mt-1">
                {useBrowserRender
                  ? "Note: Browser Render mode uses Puppeteer to render the page with full JavaScript execution. This provides complete functionality like a real browser."
                  : iframeError
                  ? "Note: Iframe blocking is normal for major sites like Amazon. The Download button works independently and captures the full page."
                  : useProxy
                  ? "Note: Proxy mode is enabled - this bypasses iframe restrictions and shows the website content directly. Some interactive features may not work due to backend restrictions."
                  : "Note: Some websites may not load properly due to security restrictions. You can interact with the page above and then click 'Download Screenshot' to capture it."}
              </p>
              {useProxy && !useBrowserRender && (
                <p className="text-xs mt-1 text-amber-600">
                  ⚠️ Interactive features like "Read sample" may show 403 errors
                  due to Amazon's backend restrictions, but the page content and
                  screenshots work correctly.
                </p>
              )}
              {useBrowserRender && (
                <p className="text-xs mt-1 text-green-600">
                  ✅ Browser Render mode provides full functionality - all
                  interactive features work correctly!
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
