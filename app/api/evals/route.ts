import { NextResponse } from "next/server"
import { EVALS_DIR } from "@/lib/utils"
import fs from "fs/promises"
import path from "path"

export async function GET() {
  try {
    const files = await fs.readdir(EVALS_DIR)
    const jsonFiles = files.filter((f) => f.endsWith(".json"))

    const evals = await Promise.all(
      jsonFiles.map(async (filename) => {
        const content = await fs.readFile(
          path.join(EVALS_DIR, filename),
          "utf-8"
        )
        return JSON.parse(content)
      })
    )

    return NextResponse.json({ success: true, data: evals })
  } catch (err) {
    console.error(err)
    return NextResponse.json(
      { success: false, error: "Failed to load evals" },
      { status: 500 }
    )
  }
}
