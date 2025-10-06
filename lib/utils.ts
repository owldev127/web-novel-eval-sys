import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { promises as fs } from "fs";
import path from "path";
import { NovelData} from '@/app/scraping/page';
import { EvaluationResult } from '@/app/evaluation/page';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


export const STORE_DIR = path.resolve("storage")
export const WORKS_DIR = path.join(STORE_DIR, "works");
export const EVALS_DIR = path.join(STORE_DIR, "evals");

export function toNovelData(obj: any): NovelData {
  return {
    id: obj.work_id ?? "",
    title: obj.title ?? "",
    author: obj.author ?? "",
    url: obj.work_url ?? "",
    summary: obj.overview.description ?? "",
    genre: obj.genre ?? "恋愛",
    keywords: Array.isArray(obj.keywords) ? obj.keywords : ["学園", "青春", "恋愛", "日常"],
    status: obj.status === "連載中" ? "連載中" : "完結済", // Fallback to "完結済"
    chapters: typeof obj.scraped_episodes === "number" ? obj.scraped_episodes : 0,
    wordCount: typeof obj.metrics.total_chars === "number" ? obj.metrics.total_chars : 0,
    lastUpdated: obj.lastUpdated ?? "2024-01-15",
    previewText: obj.previewText ?? "僕の名前は田中一郎。どこにでもいる平凡な高校二年生だ。毎日同じような日常を送っていた僕の生活が変わったのは、隣の家に引っ越してきた少女との出会いがきっかけだった...",
  }
}


export function convertJSONToEvals(obj: any): EvaluationResult[] {
  if (!Array.isArray(obj)) return []

  return obj.map((item, index) => ({
    id: item.id ?? index + 1,
    name: item.name ?? "未設定",
    confidence: typeof item.confidence === "number" ? item.confidence : 0,
    score: typeof item.score === "number" ? item.score : 0,
    maxScore: typeof item.maxScore === "number" ? item.maxScore : 10,
    reason: item.reason ?? "",
  }))
}

export function toEvalData(obj: any): EvaluationResult[] {
  const scoreLabels: Record<string, string> = {
    tempo: "構成・テンポ",
    characters: "キャラクター",
    style: "文章力",
    worldbuilding: "世界観・設定",
    target_fit: "ターゲット適合度",
  }
  const reasons = [...(obj?.comments?.weaknesses ?? []), ...(obj?.comments?.strengths ?? [])]

  return Object.entries(obj.scores).map(([key, value], index) => ({
    id: index + 1,
    name: scoreLabels[key] ?? key,
    confidence: Math.floor(Math.random() * 10) + 1,
    score: typeof value === "number" ? Math.round(value) : 0,
    maxScore: 10,
    reason: reasons[index] ?? obj.final_summary ?? "",
  }))
}

export function truncateVisible(text: string, maxWidth: number): string {
  let width = 0
  let result = ""

  for (const char of text) {
    // Treat wide CJK/emoji as 2, Latin etc. as 1
    const charWidth = /[\u3000-\u9FFF\uFF00-\uFFEF]/.test(char) ? 2 : 1
    if (width + charWidth > maxWidth) break

    result += char
    width += charWidth
  }

  return result + (width >= maxWidth ? "…" : "")
}