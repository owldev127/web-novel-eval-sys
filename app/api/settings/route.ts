import { NextResponse } from "next/server"
import fs from "fs/promises"
import path from "path"
import { STORE_DIR } from "@/lib/utils"

const SETTINGS_DIR = path.join(STORE_DIR, "settings")
const SETTINGS_FILE = path.join(SETTINGS_DIR, "settings.json")

export async function GET() {
  try {
    // Check if settings file exists
    try {
      await fs.access(SETTINGS_FILE)
    } catch {
      // File doesn't exist, return empty settings
      return NextResponse.json({
        success: true,
        data: [],
      })
    }

    const content = await fs.readFile(SETTINGS_FILE, "utf-8")
    const settings = JSON.parse(content)

    return NextResponse.json({ success: true, data: settings })
  } catch (err) {
    console.error("Error reading settings:", err)
    return NextResponse.json(
      {
        success: false,
        error: "Failed to load settings",
      },
      { status: 500 }
    )
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { settings } = body

    // Ensure settings directory exists
    await fs.mkdir(SETTINGS_DIR, { recursive: true })

    // Write settings to file
    await fs.writeFile(
      SETTINGS_FILE,
      JSON.stringify(settings, null, 2),
      "utf-8"
    )

    return NextResponse.json({ success: true })
  } catch (err) {
    console.error("Error saving settings:", err)
    return NextResponse.json(
      {
        success: false,
        error: "Failed to save settings",
      },
      { status: 500 }
    )
  }
}
