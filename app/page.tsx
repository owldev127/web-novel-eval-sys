import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, Brain, Settings, List, ArrowRight } from "lucide-react"
import Link from "next/link"

const features = [
  {
    title: "作品データ取得",
    description: "小説家になろうから作品データを自動取得",
    icon: FileText,
    href: "/scraping",
    color: "text-blue-600",
  },
  {
    title: "AI評価",
    description: "設定した評価項目に基づいてAIが作品を評価",
    icon: Brain,
    href: "/evaluation",
    color: "text-purple-600",
  },
  {
    title: "評価設定",
    description: "評価項目とプロンプトをカスタマイズ",
    icon: Settings,
    href: "/settings",
    color: "text-green-600",
  },
  {
    title: "評価済み作品",
    description: "評価結果の確認と管理",
    icon: List,
    href: "/results",
    color: "text-orange-600",
  },
]

export default function HomePage() {
  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-balance">小説AI評価システム</h1>
          <p className="text-xl text-muted-foreground text-pretty max-w-2xl mx-auto">
            小説家になろうの作品を自動取得し、AIによる多段階評価を実行。
            評価項目のカスタマイズから結果管理まで、一貫したワークフローを提供します。
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature) => (
            <Card
              key={feature.title}
              className="group hover:shadow-lg transition-all duration-200 border-2 hover:border-primary/20"
            >
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <feature.icon className={`w-5 h-5 ${feature.color}`} />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <CardDescription className="text-base mb-4">{feature.description}</CardDescription>
                <Link href={feature.href}>
                  <Button
                    variant="outline"
                    className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors bg-transparent"
                  >
                    開始する
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Start */}
        <Card className="bg-gradient-to-r from-primary/5 to-accent/5 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              クイックスタート
            </CardTitle>
            <CardDescription>3ステップで評価を開始できます</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center space-y-2">
                <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center mx-auto text-sm font-semibold">
                  1
                </div>
                <h3 className="font-medium">データ取得</h3>
                <p className="text-sm text-muted-foreground">作品URLを入力して基本情報を取得</p>
              </div>
              <div className="text-center space-y-2">
                <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center mx-auto text-sm font-semibold">
                  2
                </div>
                <h3 className="font-medium">評価設定</h3>
                <p className="text-sm text-muted-foreground">評価項目とAIプロンプトを設定</p>
              </div>
              <div className="text-center space-y-2">
                <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center mx-auto text-sm font-semibold">
                  3
                </div>
                <h3 className="font-medium">AI評価実行</h3>
                <p className="text-sm text-muted-foreground">AIによる自動評価と結果確認</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
