"use client"

import { useState } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Separator } from "@/components/ui/separator"
import { List, Search, Filter, Eye, CheckCircle, XCircle, Star, Calendar, User } from "lucide-react"

interface EvaluationResult {
  id: number
  workTitle: string
  author: string
  evaluationStage: string
  evaluationDate: string
  totalScore: number
  maxScore: number
  isPassed: boolean
  details: {
    criteriaName: string
    score: number
    maxScore: number
    reason: string
  }[]
}

const mockResults: EvaluationResult[] = [
  {
    id: 1,
    workTitle: "アラギさんのお隣さん",
    author: "山田太郎",
    evaluationStage: "第一段階",
    evaluationDate: "2024-01-15",
    totalScore: 22,
    maxScore: 30,
    isPassed: true,
    details: [
      { criteriaName: "構成・プロット", score: 8, maxScore: 10, reason: "物語の構成が良く練られている" },
      { criteriaName: "キャラクター", score: 7, maxScore: 10, reason: "主人公は魅力的だが、サブキャラの個性が薄い" },
      { criteriaName: "文章力", score: 7, maxScore: 10, reason: "読みやすいが表現力に改善の余地あり" },
    ],
  },
  {
    id: 2,
    workTitle: "アラギさんのお隣さん",
    author: "山田太郎",
    evaluationStage: "第二段階",
    evaluationDate: "2024-01-16",
    totalScore: 18,
    maxScore: 30,
    isPassed: false,
    details: [
      { criteriaName: "独創性", score: 6, maxScore: 10, reason: "ありがちな設定だが、独自の視点がある" },
      { criteriaName: "世界観", score: 7, maxScore: 10, reason: "学園設定は一般的だが、細部の描写が丁寧" },
      { criteriaName: "テーマ性", score: 5, maxScore: 10, reason: "テーマが曖昧で、メッセージ性が弱い" },
    ],
  },
  {
    id: 3,
    workTitle: "魔法学園の落ちこぼれ",
    author: "佐藤花子",
    evaluationStage: "第一段階",
    evaluationDate: "2024-01-14",
    totalScore: 25,
    maxScore: 30,
    isPassed: true,
    details: [
      { criteriaName: "構成・プロット", score: 9, maxScore: 10, reason: "非常に良く構成された物語展開" },
      { criteriaName: "キャラクター", score: 8, maxScore: 10, reason: "個性豊かなキャラクターが魅力的" },
      { criteriaName: "文章力", score: 8, maxScore: 10, reason: "表現力豊かで読みやすい文章" },
    ],
  },
  {
    id: 4,
    workTitle: "異世界転生した僕の冒険記",
    author: "鈴木次郎",
    evaluationStage: "第一段階",
    evaluationDate: "2024-01-13",
    totalScore: 15,
    maxScore: 30,
    isPassed: false,
    details: [
      { criteriaName: "構成・プロット", score: 5, maxScore: 10, reason: "展開が予想しやすく、新鮮味に欠ける" },
      { criteriaName: "キャラクター", score: 6, maxScore: 10, reason: "主人公は平凡で、他キャラも類型的" },
      { criteriaName: "文章力", score: 4, maxScore: 10, reason: "文章が単調で、表現力に課題がある" },
    ],
  },
  {
    id: 5,
    workTitle: "魔法学園の落ちこぼれ",
    author: "佐藤花子",
    evaluationStage: "第二段階",
    evaluationDate: "2024-01-17",
    totalScore: 23,
    maxScore: 30,
    isPassed: true,
    details: [
      { criteriaName: "独創性", score: 8, maxScore: 10, reason: "魔法学園という設定に新しい解釈を加えている" },
      { criteriaName: "世界観", score: 8, maxScore: 10, reason: "魔法システムが詳細で一貫性がある" },
      { criteriaName: "テーマ性", score: 7, maxScore: 10, reason: "成長と友情のテーマが明確に描かれている" },
    ],
  },
]

export default function ResultsPage() {
  const [results, setResults] = useState<EvaluationResult[]>(mockResults)
  const [searchTerm, setSearchTerm] = useState("")
  const [stageFilter, setStageFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [selectedResult, setSelectedResult] = useState<EvaluationResult | null>(null)

  const filteredResults = results.filter((result) => {
    const matchesSearch =
      result.workTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.author.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStage = stageFilter === "all" || result.evaluationStage === stageFilter
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "passed" && result.isPassed) ||
      (statusFilter === "failed" && !result.isPassed)

    return matchesSearch && matchesStage && matchesStatus
  })

  const getScoreColor = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100
    if (percentage >= 80) return "text-success"
    if (percentage >= 60) return "text-warning"
    return "text-destructive"
  }

  const getScorePercentage = (score: number, maxScore: number) => {
    return Math.round((score / maxScore) * 100)
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-balance">評価済み作品</h1>
          <p className="text-muted-foreground text-pretty">AI評価が完了した作品の結果を確認・管理できます。</p>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-primary" />
              フィルター・検索
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">作品検索</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="作品名・作者名で検索"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">評価段階</label>
                <Select value={stageFilter} onValueChange={setStageFilter}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">すべて</SelectItem>
                    <SelectItem value="第一段階">第一段階</SelectItem>
                    <SelectItem value="第二段階">第二段階</SelectItem>
                    <SelectItem value="第三段階">第三段階</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">合否</label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">すべて</SelectItem>
                    <SelectItem value="passed">合格</SelectItem>
                    <SelectItem value="failed">不合格</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">アクション</label>
                <Button variant="outline" className="w-full bg-transparent">
                  CSVエクスポート
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">{filteredResults.length}</div>
              <div className="text-sm text-muted-foreground">総評価数</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-success">{filteredResults.filter((r) => r.isPassed).length}</div>
              <div className="text-sm text-muted-foreground">合格</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-destructive">
                {filteredResults.filter((r) => !r.isPassed).length}
              </div>
              <div className="text-sm text-muted-foreground">不合格</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-warning">
                {Math.round((filteredResults.filter((r) => r.isPassed).length / filteredResults.length) * 100) || 0}%
              </div>
              <div className="text-sm text-muted-foreground">合格率</div>
            </CardContent>
          </Card>
        </div>

        {/* Results Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <List className="w-5 h-5 text-primary" />
              評価結果一覧
            </CardTitle>
            <CardDescription>{filteredResults.length}件の評価結果を表示中</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>作品名</TableHead>
                    <TableHead>評価段階</TableHead>
                    <TableHead>評価スコア</TableHead>
                    <TableHead>合否</TableHead>
                    <TableHead>評価日</TableHead>
                    <TableHead>詳細</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredResults.map((result) => (
                    <TableRow key={result.id}>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="font-medium">{result.workTitle}</div>
                          <div className="flex items-center gap-1 text-sm text-muted-foreground">
                            <User className="w-3 h-3" />
                            {result.author}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{result.evaluationStage}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className={`font-semibold ${getScoreColor(result.totalScore, result.maxScore)}`}>
                            {result.totalScore}/{result.maxScore}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {getScorePercentage(result.totalScore, result.maxScore)}%
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={result.isPassed ? "default" : "destructive"} className="gap-1">
                          {result.isPassed ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {result.isPassed ? "合格" : "不合格"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm">
                          <Calendar className="w-3 h-3 text-muted-foreground" />
                          {result.evaluationDate}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="ghost" size="sm" onClick={() => setSelectedResult(result)}>
                              <Eye className="w-4 h-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                            <DialogHeader>
                              <DialogTitle className="flex items-center gap-2">
                                <Star className="w-5 h-5 text-primary" />
                                評価詳細: {result.workTitle}
                              </DialogTitle>
                              <DialogDescription>{result.evaluationStage}の詳細評価結果</DialogDescription>
                            </DialogHeader>

                            {selectedResult && (
                              <div className="space-y-6">
                                {/* Overall Score */}
                                <Card
                                  className={`border-2 ${selectedResult.isPassed ? "border-success/20 bg-success/5" : "border-destructive/20 bg-destructive/5"}`}
                                >
                                  <CardContent className="p-4">
                                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                                      <div>
                                        <div className="text-2xl font-bold text-primary">
                                          {selectedResult.totalScore}
                                        </div>
                                        <div className="text-sm text-muted-foreground">総合スコア</div>
                                      </div>
                                      <div>
                                        <div className="text-2xl font-bold text-muted-foreground">
                                          {selectedResult.maxScore}
                                        </div>
                                        <div className="text-sm text-muted-foreground">満点</div>
                                      </div>
                                      <div>
                                        <div className="text-2xl font-bold text-warning">
                                          {getScorePercentage(selectedResult.totalScore, selectedResult.maxScore)}%
                                        </div>
                                        <div className="text-sm text-muted-foreground">達成率</div>
                                      </div>
                                      <div>
                                        <Badge
                                          variant={selectedResult.isPassed ? "default" : "destructive"}
                                          className="text-lg px-3 py-1"
                                        >
                                          {selectedResult.isPassed ? "合格" : "不合格"}
                                        </Badge>
                                      </div>
                                    </div>
                                  </CardContent>
                                </Card>

                                {/* Detailed Scores */}
                                <div className="space-y-4">
                                  <h3 className="text-lg font-semibold">項目別評価</h3>
                                  {selectedResult.details.map((detail, index) => (
                                    <Card key={index} className="border-l-4 border-l-primary/30">
                                      <CardContent className="p-4">
                                        <div className="flex items-start justify-between gap-4 mb-3">
                                          <h4 className="font-semibold text-lg">{detail.criteriaName}</h4>
                                          <Badge
                                            variant={
                                              getScorePercentage(detail.score, detail.maxScore) >= 70
                                                ? "default"
                                                : "secondary"
                                            }
                                          >
                                            {detail.score}/{detail.maxScore}
                                          </Badge>
                                        </div>
                                        <div className="space-y-2">
                                          <div className="w-full bg-muted rounded-full h-2">
                                            <div
                                              className="bg-primary h-2 rounded-full transition-all duration-300"
                                              style={{ width: `${getScorePercentage(detail.score, detail.maxScore)}%` }}
                                            />
                                          </div>
                                          <p className="text-sm text-muted-foreground leading-relaxed">
                                            {detail.reason}
                                          </p>
                                        </div>
                                      </CardContent>
                                    </Card>
                                  ))}
                                </div>

                                {/* Metadata */}
                                <Separator />
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <span className="font-medium">作者:</span> {selectedResult.author}
                                  </div>
                                  <div>
                                    <span className="font-medium">評価日:</span> {selectedResult.evaluationDate}
                                  </div>
                                </div>
                              </div>
                            )}
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {filteredResults.length === 0 && (
              <div className="text-center py-8">
                <List className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-muted-foreground mb-2">評価結果が見つかりません</h3>
                <p className="text-sm text-muted-foreground">検索条件を変更するか、新しい評価を実行してください</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
