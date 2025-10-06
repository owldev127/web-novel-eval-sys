"use client"

import { useEffect, useState } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { FileText, Download, ExternalLink, Clock, User, BookOpen, Hash } from "lucide-react"
import { toNovelData } from "@/lib/utils"
import { useRouter } from "next/navigation"

export interface NovelData {
  id: string
  title: string
  author: string
  url: string
  summary: string
  genre: string
  keywords: string[]
  status: "連載中" | "完結済"
  chapters: number
  wordCount: number
  lastUpdated: string
  previewText: string
}

export default function ScrapingPage() {
  const [scrapingUrl, setScrapingUrl] = useState("https://syosetu.com/")
  const [workUrl, setWorkUrl] = useState("")
  const [workId, setWorkId] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [scrapedData, setScrapedData] = useState<NovelData | null>(null)
  const [scrapeRawData, setScrapRawData] = useState("")
  const [savedNovels, setSavedNovels] = useState<NovelData[]>([])
  const router = useRouter()

  const handleScrape = async () => {
    setIsLoading(true)
    const parts = workUrl.split("/").filter(Boolean);
    const workId = parts[parts.length - 1];
    const source = scrapingUrl.includes("syosetu")
      ? "syosetu"
      : workUrl.includes("kakuyomu")
      ? "kakuyomu"
      : "unknown";

    if (source === 'unknown') {
      alert("対応していないウェブサイトです")
      setIsLoading(false)
      return
    }

    try {
      const res = await fetch(`/api/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job: 'scrap',
          params: {
            source: source,
            workId: workId,
            episodes: 1
          }}
        )
      });

      const json = await res.json();
      if (json.success) {
        setScrapRawData(json.data)
        setScrapedData(toNovelData(json.data))
        setWorkId(workId)
      } else {
        alert("小説のスクレイピングに失敗しました")
      }

    } catch (err) {
      alert("通信エラーが発生しました")
      console.error(err)
    }

    setIsLoading(false)
  }

  const handleSave = async () => {
    if (!scrapedData) return

    try {
      const res = await fetch("/api/novels", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ novel: scrapeRawData, workId: workId }),
      })
      const json = await res.json()
      if (json.success) {
        alert("作品データを保存しました！")
        setSavedNovels(prev => [...prev, scrapedData!])
        setScrapedData(null)
        setScrapRawData("")
        setWorkId("")
        setWorkUrl("")
      } else {
        alert("保存に失敗しました")
      }
    } catch (err) {
      alert("通信エラーが発生しました")
      console.error(err)
    }
  }

  useEffect(() => {
    const loadSavedNovels = async () => {
      try {
        const res = await fetch('/api/novels')
        const json = await res.json()
        if (json.success) {
          const novelObjects = json.data.map((obj: any) => toNovelData(obj))
          setSavedNovels(novelObjects)
        } else {
          console.log("Failed to load novel data", json.error)
        }
      } catch (e) {
        console.error("Error fetching saved novels", e)
      }
    }

    loadSavedNovels()
  }, [])

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-balance">作品データ取得</h1>
          <p className="text-muted-foreground text-pretty">
            小説家になろうから作品情報を自動取得し、データベースに保存します。
          </p>
        </div>

        {/* Scraping Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="w-5 h-5 text-primary" />
              データ取得
            </CardTitle>
            <CardDescription>作品URLを入力して、基本情報とコンテンツを取得します</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="scraping-site">取得サイト</Label>
                <Input
                  id="scraping-site"
                  value={scrapingUrl}
                  onChange={(e) => setScrapingUrl(e.target.value)}
                  placeholder="https://syosetu.com/"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="work-url">作品URL</Label>
                <Input
                  id="work-url"
                  value={workUrl}
                  onChange={(e) => setWorkUrl(e.target.value)}
                  placeholder="https://ncode.syosetu.com/work-id/"
                />
              </div>
            </div>
            <Button onClick={handleScrape} disabled={!workUrl || isLoading} className="w-full md:w-auto">
              {isLoading ? "取得中..." : "取得する"}
            </Button>
          </CardContent>
        </Card>

        {/* Scraped Data Display */}
        {scrapedData && (
          <Card className="border-primary/20 bg-primary/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                取得データ
              </CardTitle>
              <CardDescription>以下の情報が取得されました。確認後、保存してください。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>作品タイトル</Label>
                    <div className="p-3 bg-background rounded-md border">{scrapedData.title}</div>
                  </div>
                  <div className="space-y-2">
                    <Label>作者名</Label>
                    <div className="p-3 bg-background rounded-md border flex items-center gap-2">
                      <User className="w-4 h-4 text-muted-foreground" />
                      {scrapedData.author}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>作品URL</Label>
                    <div className="p-3 bg-background rounded-md border flex items-center gap-2">
                      <ExternalLink className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm text-primary truncate">{scrapedData.url}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>ジャンル・キーワード</Label>
                    <div className="p-3 bg-background rounded-md border">
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="secondary">{scrapedData.genre}</Badge>
                        {scrapedData.keywords.map((keyword) => (
                          <Badge key={keyword} variant="outline">
                            {keyword}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>掲載状況</Label>
                      <div className="p-3 bg-background rounded-md border">
                        <Badge variant={scrapedData.status === "完結済" ? "default" : "secondary"}>
                          {scrapedData.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>最終更新</Label>
                      <div className="p-3 bg-background rounded-md border flex items-center gap-2">
                        <Clock className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm">{scrapedData.lastUpdated}</span>
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>話数</Label>
                      <div className="p-3 bg-background rounded-md border flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm">{scrapedData.chapters}話</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>文字数</Label>
                      <div className="p-3 bg-background rounded-md border flex items-center gap-2">
                        <Hash className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm">{scrapedData.wordCount.toLocaleString()}文字</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>あらすじ</Label>
                <div className="p-4 bg-background rounded-md border">
                  <p className="text-sm leading-relaxed">{scrapedData.summary}</p>
                </div>
              </div>

              <div className="space-y-2">
                <Label>試し読みテキスト</Label>
                <div className="p-4 bg-background rounded-md border max-h-40 overflow-y-auto">
                  <p className="text-sm leading-relaxed text-muted-foreground">{scrapedData.previewText}</p>
                </div>
              </div>

              <div className="flex gap-3">
                <Button onClick={handleSave} className="flex-1 md:flex-none">
                  保存する
                </Button>
                <Button variant="outline" onClick={() => setScrapedData(null)}>
                  キャンセル
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Saved Novels List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              保存済み作品
            </CardTitle>
            <CardDescription>取得・保存された作品の一覧です</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {savedNovels.map((novel, index) => (
                <Card key={index} className="border-l-4 border-l-primary/50">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-lg">{novel.title}</h3>
                          <Badge variant={novel.status === "完結済" ? "default" : "secondary"}>{novel.status}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {novel.author}
                          </span>
                          <span className="flex items-center gap-1">
                            <BookOpen className="w-3 h-3" />
                            {novel.chapters}話
                          </span>
                          <span className="flex items-center gap-1">
                            <Hash className="w-3 h-3" />
                            {novel.wordCount.toLocaleString()}文字
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">{novel.summary}</p>
                        <div className="flex flex-wrap gap-1">
                          <Badge variant="secondary" className="text-xs">
                            {novel.genre}
                          </Badge>
                          {novel.keywords.slice(0, 3).map((keyword) => (
                            <Badge key={keyword} variant="outline" className="text-xs">
                              {keyword}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Button 
                        variant="outline" size="sm"
                      >
                        選択
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
