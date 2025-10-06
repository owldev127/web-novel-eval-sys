import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'
import { WORKS_DIR } from '@/lib/utils'

export async function GET() {
  try {
    const files = await fs.readdir(WORKS_DIR)
    const jsonFiles = files.filter(f => f.endsWith('.json'))

    const novels = await Promise.all(
      jsonFiles.map(async (filename) => {
        const content = await fs.readFile(path.join(WORKS_DIR, filename), 'utf-8')
        return JSON.parse(content)
      })
    )

    return NextResponse.json({ success: true, data: novels })
  } catch (err) {
    console.error(err)
    return NextResponse.json({ success: false, error: 'Failed to load novels' }, { status: 500 })
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const {novel, workId} = body

    const fileName = `${workId}.json`
    const savePath = path.join(WORKS_DIR, fileName)

    await fs.mkdir(WORKS_DIR, { recursive: true })
    await fs.writeFile(savePath, JSON.stringify(novel, null, 2), 'utf-8')

    return NextResponse.json({ success: true })
  } catch (err) {
    console.error(err)
    return NextResponse.json({ success: false, error: 'Failed to save novel' }, { status: 500 })
  }
}