"use client"

import { useEffect, useState } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  Brain,
  CheckCircle,
  XCircle,
  Star,
  TrendingUp,
  AlertCircle,
} from "lucide-react"
import { NovelData } from "../scraping/page"
import {
  convertJSONToEvals,
  toEvalData,
  toNovelData,
  truncateVisible,
} from "@/lib/utils"

export interface EvaluationResult {
  id: number
  name: string
  confidence: number
  score: number
  maxScore: number
  reason: string
}

const evaluationStages = [
  { value: "first", label: "第一段階", description: "基本的な評価項目" },
  { value: "second", label: "第二段階", description: "詳細な分析" },
  { value: "third", label: "第三段階", description: "総合評価" },
]

const aiModels = [
  { value: "chatgpt", label: "OpenAI", description: "OpenAI の最新モデル" },
  // { value: "claude", label: "Claude 3", description: "Anthropic の高性能モデル" },
  {
    value: "gemini",
    label: "Gemini Pro",
    description: "Google の多機能モデル",
  },
  {
    value: "deepseek",
    label: "DeepSeek",
    description: "DeepSeek のマルチモーダル対応モデル",
  },
  { value: "phi", label: "Phi 4", description: "Microsoft の軽量モデル" },
  { value: "qwen", label: "Qwen 3", description: "Alibaba の大規模モデル" },
]

export default function EvaluationPage() {
  const [novels, setNovels] = useState<NovelData[]>([])
  const [selectedNovel, setSelectedNovel] = useState("")
  const [selectedStage, setSelectedStage] = useState("")
  const [selectedModel, setSelectedModel] = useState("")
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluationResults, setEvaluationResults] = useState<
    EvaluationResult[] | null
  >(null)
  const [totalScore, setTotalScore] = useState(0)
  const [maxTotalScore, setMaxTotalScore] = useState(30)
  const [passingScore, setPassingScore] = useState(18)

  const handleEvaluate = async () => {
    setIsEvaluating(true)

    try {
      const res = await fetch("/api/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job: "eval",
          params: {
            agent: selectedModel,
            workId: selectedNovel,
            stageNum: selectedStage,
          },
        }),
      })

      const json = await res.json()
      if (json.success) {
        const evals = toEvalData(json.data)
        setEvaluationResults(evals)
        const total = evals.reduce((sum, result) => sum + result.score, 0)
        setTotalScore(total)
      } else {
        alert("評価に失敗しました")
      }
    } catch (err) {
      alert("評価に失敗しました")
      console.log(err)
    }

    setIsEvaluating(false)
  }

  const handleSaveResults = async () => {
    try {
      // Get the selected novel data to extract title and author
      const selectedNovelData = novels.find(
        (novel) => novel.id === selectedNovel
      )

      const res = await fetch(`/api/evals/${selectedNovel}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          evals: evaluationResults,
          workId: selectedNovel,
          workTitle: selectedNovelData?.title || "",
          author: selectedNovelData?.author || "",
          stage: selectedStage,
          stageLabel: evaluationStages.find((o) => o.value === selectedStage)
            ?.label,
          totalScore,
          passingScore,
        }),
      })

      const json = await res.json()

      if (json.success) {
        alert("評価結果を保存しました！")
      } else {
        console.error("保存失敗:", json.error)
        alert("評価結果の保存に失敗しました。")
      }
    } catch (error) {
      console.error("保存エラー:", error)
      alert("通信エラーが発生しました。")
    }
  }

  const getScoreColor = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100
    if (percentage >= 80) return "text-success"
    if (percentage >= 60) return "text-warning"
    return "text-destructive"
  }

  const getScoreBadgeVariant = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100
    if (percentage >= 80) return "default"
    if (percentage >= 60) return "secondary"
    return "destructive"
  }

  const isPassed = totalScore >= passingScore

  useEffect(() => {
    const fetchNovels = async () => {
      try {
        const res = await fetch("/api/novels")
        const json = await res.json()

        if (json.success) {
          const normalized = json.data.map((item: any) => toNovelData(item))
          setNovels(normalized)
        } else {
          console.error("Failed to fetch novels", json.error)
        }
      } catch (err) {
        console.error("Error fetching novel data", err)
      }
    }

    fetchNovels()
  }, [])

  // useEffect(() => {
  //   const fetchEvalData = async () => {
  //     if (!selectedNovel) return

  //     try {
  //       const res = await fetch(`/api/evals/${selectedNovel}`)
  //       const json = await res.json()

  //       if (json.success && json.data) {
  //         const parsed = convertJSONToEvals(json.data)
  //         setEvaluationResults(parsed)
  //         // Optionally set total score, etc.
  //         const total = parsed.reduce((sum, result) => sum + result.score, 0)
  //         setTotalScore(total)
  //       } else {
  //         console.warn("No evaluation found for selected work.")
  //         setEvaluationResults(null)
  //       }
  //     } catch (err) {
  //       console.error("Error loading evaluation:", err)
  //       setEvaluationResults(null)
  //     }
  //   }

  //   fetchEvalData()
  // }, [selectedNovel])

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-balance">AI評価</h1>
          <p className="text-muted-foreground text-pretty">
            保存された作品を選択し、設定した評価項目に基づいてAIによる評価を実行します。
          </p>
        </div>

        {/* Evaluation Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              評価設定
            </CardTitle>
            <CardDescription>
              評価する作品、段階、AIモデルを選択してください
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>作品タイトル</Label>
                <Select value={selectedNovel} onValueChange={setSelectedNovel}>
                  <SelectTrigger>
                    <SelectValue placeholder="評価する作品を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    {novels.map((novel) => (
                      <SelectItem key={novel.id} value={novel.id.toString()}>
                        <div className="flex flex-col items-start">
                          <span className="font-medium">
                            {truncateVisible(novel.title, 16)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {novel.author}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>評価段階</Label>
                <Select value={selectedStage} onValueChange={setSelectedStage}>
                  <SelectTrigger>
                    <SelectValue placeholder="評価段階を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    {evaluationStages.map((stage) => (
                      <SelectItem key={stage.value} value={stage.value}>
                        <div className="flex flex-col items-start">
                          <span className="font-medium">{stage.label}</span>
                          <span className="text-xs text-muted-foreground">
                            {stage.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>AIモデル</Label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger>
                  <SelectValue placeholder="使用するAIモデルを選択" />
                </SelectTrigger>
                <SelectContent>
                  {aiModels.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      <div className="flex flex-col items-start">
                        <span className="font-medium">{model.label}</span>
                        <span className="text-xs text-muted-foreground">
                          {model.description}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={handleEvaluate}
              disabled={
                !selectedNovel ||
                !selectedStage ||
                !selectedModel ||
                isEvaluating
              }
              className="w-full md:w-auto"
            >
              {isEvaluating ? "評価中..." : "評価する"}
            </Button>
          </CardContent>
        </Card>

        {/* Evaluation Progress */}
        {isEvaluating && (
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <Brain className="w-5 h-5 text-primary animate-pulse" />
                <span className="font-medium">AI評価を実行中...</span>
              </div>
              <Progress value={66} className="mb-2" />
              <p className="text-sm text-muted-foreground">
                評価項目を順次処理しています。しばらくお待ちください。
              </p>
            </CardContent>
          </Card>
        )}

        {/* Evaluation Results */}
        {evaluationResults && (
          <div className="space-y-6">
            {/* Overall Score */}
            <Card
              className={`border-2 ${
                isPassed
                  ? "border-success/20 bg-success/5"
                  : "border-destructive/20 bg-destructive/5"
              }`}
            >
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {isPassed ? (
                      <CheckCircle className="w-5 h-5 text-success" />
                    ) : (
                      <XCircle className="w-5 h-5 text-destructive" />
                    )}
                    評価結果
                  </div>
                  <Badge
                    variant={isPassed ? "default" : "destructive"}
                    className="text-lg px-3 py-1"
                  >
                    {isPassed ? "合格" : "不合格"}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center space-y-2">
                    <div className="text-3xl font-bold text-primary">
                      {totalScore}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      総合スコア
                    </div>
                  </div>
                  <div className="text-center space-y-2">
                    <div className="text-3xl font-bold text-muted-foreground">
                      {maxTotalScore}
                    </div>
                    <div className="text-sm text-muted-foreground">満点</div>
                  </div>
                  <div className="text-center space-y-2">
                    <div className="text-3xl font-bold text-warning">
                      {passingScore}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      合格ライン
                    </div>
                  </div>
                </div>
                <div className="mt-4">
                  <Progress
                    value={(totalScore / maxTotalScore) * 100}
                    className="h-3"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>0</span>
                    <span className="text-warning">
                      合格ライン: {passingScore}
                    </span>
                    <span>{maxTotalScore}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Results */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-primary" />
                  詳細評価
                </CardTitle>
                <CardDescription>各評価項目の詳細結果</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {evaluationResults.map((result, index) => (
                  <div key={result.id}>
                    <Card className="border-l-4 border-l-primary/30">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-4 mb-3">
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg mb-1">
                              {result.name}
                            </h3>
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <TrendingUp className="w-3 h-3" />
                                確信度: {result.confidence}
                              </span>
                              <span className="flex items-center gap-1">
                                <Star className="w-3 h-3" />
                                スコア: {result.score}/{result.maxScore}
                              </span>
                            </div>
                          </div>
                          <Badge
                            variant={getScoreBadgeVariant(
                              result.score,
                              result.maxScore
                            )}
                          >
                            {result.score}/{result.maxScore}
                          </Badge>
                        </div>
                        <div className="mb-3">
                          <Progress
                            value={(result.score / result.maxScore) * 100}
                            className="h-2"
                          />
                        </div>
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {result.reason}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    {index < evaluationResults.length - 1 && (
                      <Separator className="my-4" />
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={handleSaveResults}
                className="flex-1 md:flex-none"
              >
                結果を保存
              </Button>
              <Button
                variant="outline"
                onClick={() => setEvaluationResults(null)}
              >
                新しい評価
              </Button>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  )
}
