"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  FileText,
  Brain,
  Settings,
  List,
  Menu,
  X,
  Download,
} from "lucide-react"

const navigation = [
  {
    name: "作品データ取得",
    href: "/scraping",
    icon: FileText,
    description: "小説データの取得",
  },
  {
    name: "AI評価",
    href: "/evaluation",
    icon: Brain,
    description: "AI による作品評価",
  },
  {
    name: "評価設定",
    href: "/settings",
    icon: Settings,
    description: "評価項目の設定",
  },
  {
    name: "評価済み作品",
    href: "/results",
    icon: List,
    description: "評価結果の一覧",
  },
  {
    name: "画像ダウンロード",
    href: "/download",
    icon: Download,
    description: "サイトのスクリーンショット取得",
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <Card className="h-screen w-64 border-r bg-sidebar/50 backdrop-blur-sm">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-sidebar-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Brain className="w-4 h-4 text-primary-foreground" />
            </div>
            {!isCollapsed && (
              <div>
                <h1 className="text-lg font-semibold text-sidebar-foreground">
                  Novel AI
                </h1>
                <p className="text-xs text-muted-foreground">評価システム</p>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-sidebar-foreground hover:bg-sidebar-accent"
          >
            {isCollapsed ? (
              <Menu className="w-4 h-4" />
            ) : (
              <X className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link key={item.name} href={item.href}>
                <Button
                  variant={isActive ? "default" : "ghost"}
                  className={cn(
                    "w-full justify-start gap-3 h-12",
                    isActive
                      ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  )}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  {!isCollapsed && (
                    <div className="flex flex-col items-start">
                      <span className="text-sm font-medium">{item.name}</span>
                      <span className="text-xs opacity-70">
                        {item.description}
                      </span>
                    </div>
                  )}
                </Button>
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-sidebar-border">
          <div className="text-xs text-muted-foreground text-center">
            Novel Evaluation System v1.0
          </div>
        </div>
      </div>
    </Card>
  )
}
