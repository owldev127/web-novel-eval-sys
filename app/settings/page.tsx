"use client"

import { useState } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Settings, Plus, Trash2, Save, Target, Edit3 } from "lucide-react"

interface EvaluationCriteria {
  id: number
  name: string
  prompt: string
  minScore: number
  maxScore: number
}

interface StageSettings {
  stage: string
  label: string
  criteria: EvaluationCriteria[]
  passingScore: number
  totalMaxScore: number
}

const initialSettings: StageSettings[] = [
  {
    stage: "first",
    label: "第一段階",
    criteria: [
      {
        id: 1,
        name: "構成・プロット",
        prompt:
          "物語の構成、プロットの完成度を評価してください。起承転結の明確さ、展開の自然さ、読者を引き込む力を重視してください。",
        minScore: 1,
        maxScore: 10,
      },
      {
        id: 2,
        name: "キャラクター",
        prompt:
          "登場人物の魅力度、個性の明確さ、成長性を評価してください。主人公とサブキャラクターのバランスも考慮してください。",
        minScore: 1,
        maxScore: 10,
      },
      {
        id: 3,
        name: "文章力",
        prompt:
          "文章の読みやすさ、表現力、語彙の豊富さを評価してください。誤字脱字や文法的な正確性も含めて判断してください。",
        minScore: 1,
        maxScore: 10,
      },
    ],
    passingScore: 18,
    totalMaxScore: 30,
  },
  {
    stage: "second",
    label: "第二段階",
    criteria: [
      {
        id: 4,
        name: "独創性",
        prompt:
          "作品のオリジナリティ、新しいアイデアや視点の有無を評価してください。既存作品との差別化ができているかを重視してください。",
        minScore: 1,
        maxScore: 10,
      },
      {
        id: 5,
        name: "世界観",
        prompt:
          "作品の世界観の構築度、設定の一貫性、リアリティを評価してください。読者が没入できる世界が作られているかを判断してください。",
        minScore: 1,
        maxScore: 10,
      },
      {
        id: 6,
        name: "テーマ性",
        prompt:
          "作品が伝えたいメッセージやテーマの明確さ、深さを評価してください。読者に与える影響や考えさせる力を重視してください。",
        minScore: 1,
        maxScore: 10,
      },
    ],
    passingScore: 20,
    totalMaxScore: 30,
  },
  {
    stage: "third",
    label: "第三段階",
    criteria: [
      {
        id: 7,
        name: "総合完成度",
        prompt:
          "作品全体の完成度を総合的に評価してください。すべての要素がバランス良く組み合わされているかを判断してください。",
        minScore: 1,
        maxScore: 15,
      },
      {
        id: 8,
        name: "商業性",
        prompt:
          "作品の商業的な価値、読者への訴求力、市場での競争力を評価してください。出版やメディア化の可能性を考慮してください。",
        minScore: 1,
        maxScore: 15,
      },
    ],
    passingScore: 20,
    totalMaxScore: 30,
  },
]

export default function SettingsPage() {
  const [settings, setSettings] = useState<StageSettings[]>(initialSettings)
  const [activeStage, setActiveStage] = useState("first")
  const [editingCriteria, setEditingCriteria] = useState<number | null>(null)

  const currentStageSettings = settings.find((s) => s.stage === activeStage)!

  const addCriteria = () => {
    const newCriteria: EvaluationCriteria = {
      id: Date.now(),
      name: "新しい評価項目",
      prompt: "評価の詳細な指示を入力してください...",
      minScore: 1,
      maxScore: 10,
    }

    setSettings((prev) =>
      prev.map((stage) =>
        stage.stage === activeStage
          ? {
              ...stage,
              criteria: [...stage.criteria, newCriteria],
              totalMaxScore: stage.totalMaxScore + 10,
            }
          : stage,
      ),
    )
    setEditingCriteria(newCriteria.id)
  }

  const updateCriteria = (criteriaId: number, field: keyof EvaluationCriteria, value: string | number) => {
    setSettings((prev) =>
      prev.map((stage) =>
        stage.stage === activeStage
          ? {
              ...stage,
              criteria: stage.criteria.map((criteria) =>
                criteria.id === criteriaId ? { ...criteria, [field]: value } : criteria,
              ),
            }
          : stage,
      ),
    )
  }

  const deleteCriteria = (criteriaId: number) => {
    const criteriaToDelete = currentStageSettings.criteria.find((c) => c.id === criteriaId)
    if (!criteriaToDelete) return

    setSettings((prev) =>
      prev.map((stage) =>
        stage.stage === activeStage
          ? {
              ...stage,
              criteria: stage.criteria.filter((c) => c.id !== criteriaId),
              totalMaxScore: stage.totalMaxScore - criteriaToDelete.maxScore,
            }
          : stage,
      ),
    )
  }

  const updatePassingScore = (score: number) => {
    setSettings((prev) =>
      prev.map((stage) => (stage.stage === activeStage ? { ...stage, passingScore: score } : stage)),
    )
  }

  const saveSettings = () => {
    // Simulate saving to database
    alert("設定を保存しました！")
    setEditingCriteria(null)
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-balance">評価設定</h1>
          <p className="text-muted-foreground text-pretty">段階ごとの評価項目とプロンプトを設定・管理します。</p>
        </div>

        {/* Stage Tabs */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-primary" />
              評価段階設定
            </CardTitle>
            <CardDescription>各段階の評価項目を設定してください</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeStage} onValueChange={setActiveStage}>
              <TabsList className="grid w-full grid-cols-3">
                {settings.map((stage) => (
                  <TabsTrigger key={stage.stage} value={stage.stage} className="flex flex-col gap-1">
                    <span className="font-medium">{stage.label}</span>
                    <span className="text-xs text-muted-foreground">{stage.criteria.length}項目</span>
                  </TabsTrigger>
                ))}
              </TabsList>

              {settings.map((stageSettings) => (
                <TabsContent key={stageSettings.stage} value={stageSettings.stage} className="space-y-6 mt-6">
                  {/* Passing Score Setting */}
                  <Card className="border-primary/20 bg-primary/5">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                          <Target className="w-5 h-5 text-primary" />
                          <div>
                            <h3 className="font-semibold">合格ライン</h3>
                            <p className="text-sm text-muted-foreground">
                              満点{stageSettings.totalMaxScore}点中の合格基準
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            value={stageSettings.passingScore}
                            onChange={(e) => updatePassingScore(Number(e.target.value))}
                            className="w-20 text-center"
                            min={1}
                            max={stageSettings.totalMaxScore}
                          />
                          <span className="text-sm text-muted-foreground">点</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Evaluation Criteria */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold">評価項目</h3>
                      <Button onClick={addCriteria} size="sm" className="gap-2">
                        <Plus className="w-4 h-4" />
                        項目を追加
                      </Button>
                    </div>

                    {stageSettings.criteria.map((criteria, index) => (
                      <Card key={criteria.id} className="border-l-4 border-l-primary/30">
                        <CardContent className="p-4">
                          <div className="space-y-4">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex items-center gap-3">
                                <Badge variant="outline" className="text-xs">
                                  {index + 1}
                                </Badge>
                                <div className="flex-1">
                                  {editingCriteria === criteria.id ? (
                                    <Input
                                      value={criteria.name}
                                      onChange={(e) => updateCriteria(criteria.id, "name", e.target.value)}
                                      className="font-semibold"
                                      placeholder="評価項目名"
                                    />
                                  ) : (
                                    <h4 className="font-semibold text-lg">{criteria.name}</h4>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() =>
                                    setEditingCriteria(editingCriteria === criteria.id ? null : criteria.id)
                                  }
                                >
                                  <Edit3 className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => deleteCriteria(criteria.id)}
                                  className="text-destructive hover:text-destructive"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>

                            <div className="space-y-3">
                              <div>
                                <Label className="text-sm font-medium">プロンプト</Label>
                                {editingCriteria === criteria.id ? (
                                  <Textarea
                                    value={criteria.prompt}
                                    onChange={(e) => updateCriteria(criteria.id, "prompt", e.target.value)}
                                    className="mt-1 min-h-[100px]"
                                    placeholder="AIへの評価指示を詳細に記述してください..."
                                  />
                                ) : (
                                  <div className="mt-1 p-3 bg-muted rounded-md text-sm leading-relaxed">
                                    {criteria.prompt}
                                  </div>
                                )}
                              </div>

                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <Label className="text-sm font-medium">最小スコア</Label>
                                  {editingCriteria === criteria.id ? (
                                    <Input
                                      type="number"
                                      value={criteria.minScore}
                                      onChange={(e) => updateCriteria(criteria.id, "minScore", Number(e.target.value))}
                                      className="mt-1"
                                      min={1}
                                    />
                                  ) : (
                                    <div className="mt-1 p-2 bg-muted rounded-md text-sm text-center">
                                      {criteria.minScore}
                                    </div>
                                  )}
                                </div>
                                <div>
                                  <Label className="text-sm font-medium">最大スコア</Label>
                                  {editingCriteria === criteria.id ? (
                                    <Input
                                      type="number"
                                      value={criteria.maxScore}
                                      onChange={(e) => updateCriteria(criteria.id, "maxScore", Number(e.target.value))}
                                      className="mt-1"
                                      min={criteria.minScore}
                                    />
                                  ) : (
                                    <div className="mt-1 p-2 bg-muted rounded-md text-sm text-center">
                                      {criteria.maxScore}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {stageSettings.criteria.length === 0 && (
                      <Card className="border-dashed border-2 border-muted-foreground/25">
                        <CardContent className="p-8 text-center">
                          <div className="space-y-3">
                            <Settings className="w-12 h-12 text-muted-foreground mx-auto" />
                            <h3 className="text-lg font-medium text-muted-foreground">評価項目がありません</h3>
                            <p className="text-sm text-muted-foreground">
                              「項目を追加」ボタンから評価項目を追加してください
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>

                  <Separator />

                  {/* Stage Summary */}
                  <Card className="bg-accent/50">
                    <CardContent className="p-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                        <div>
                          <div className="text-2xl font-bold text-primary">{stageSettings.criteria.length}</div>
                          <div className="text-sm text-muted-foreground">評価項目数</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-primary">{stageSettings.totalMaxScore}</div>
                          <div className="text-sm text-muted-foreground">満点</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-warning">{stageSettings.passingScore}</div>
                          <div className="text-sm text-muted-foreground">合格ライン</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={saveSettings} className="gap-2">
            <Save className="w-4 h-4" />
            設定を保存
          </Button>
        </div>
      </div>
    </MainLayout>
  )
}
