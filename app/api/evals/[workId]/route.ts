import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'
import { EVALS_DIR } from '@/lib/utils'

export async function GET(
    req: Request,
    { params }: { params: { workId: string } }
) {
    const { workId } = params
    const filePath = path.join(EVALS_DIR, `${workId}.json`)

    try {
        const content = await fs.readFile(filePath, "utf-8")
        const data = JSON.parse(content)
        return NextResponse.json({ success: true, data })
    } catch (err: any) {
        console.error("Eval load failed:", err)
        const isNotFound = err.code === "ENOENT"
        return NextResponse.json(
            {
                success: false,
                error: isNotFound
                    ? `Evaluation for workId "${workId}" not found.`
                    : "Failed to load evaluation.",
            },
            { status: isNotFound ? 404 : 500 }
        )
    }
}

export async function POST(req: Request) {
    try {
        const body = await req.json()
        const { evals, workId } = body

        const fileName = `${workId}.json`
        const savePath = path.join(EVALS_DIR, fileName)

        await fs.mkdir(EVALS_DIR, { recursive: true })
        await fs.writeFile(savePath, JSON.stringify(evals, null, 2), 'utf-8')

        return NextResponse.json({ success: true })
    } catch (err) {
        console.error(err)
        return NextResponse.json({ success: false, error: 'Failed to save novel' }, { status: 500 })
    }
}