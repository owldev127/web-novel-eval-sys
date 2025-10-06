#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kakuyomu_scraper.py
カクヨム小説スクレイピングツール
カクヨムの小説作品から統合JSONを出力します

使用方法:
    python kakuyomu_scraper.py {小説ID} [話数制限]

例:
    python kakuyomu_scraper.py 16818792439429953221
    python kakuyomu_scraper.py 16818792439429953221 5

必要ライブラリ:
    pip install requests beautifulsoup4 lxml
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
from urllib.parse import urljoin, urlparse
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import math
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from scrapers.kakuyomu.list_episodes import list_episodes, list_episodes_with_session

def save_novel_json(data: Dict, work_id: str) -> str:
    """統合JSONをoutputフォルダに保存"""
    # プロジェクトルートを基準にする
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"{work_id}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"統合JSONを {filename} に保存しました")
    return filename

class KakuyomuScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
        ]
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._mount_retries(self.session)
        self.request_count = 0
        # クリーニング用の正規表現パターン（P1: ボイラープレート除去）
        self._bp_patterns: List[Tuple[str, re.Pattern]] = [
            ("stars_request", re.compile(r"[★☆]{1,}|★で称える|評価(お願いします|ください)|レビュー(を|お願いします)")),
            ("like_request", re.compile(r"♡|ハート|いいね|応援(しよう|お願いします|して|のお願い)")),
            ("sns_promo", re.compile(r"SNS|Twitter|X\s*\(|フォロー|宣伝|読了報告")),
            ("ranking", re.compile(r"(月間|週間|年間).{0,8}(ランキング|順位)|1位|上位|目標")),
            ("thanks_request", re.compile(r"お礼とお願い|お願い|ギフト|切実")),
            ("update_notice", re.compile(r"更新告知|次回更新|告知|予告")),
            ("footer_heading", re.compile(r"^\s*[★☆]{4,}.*[★☆]{4,}\s*$")),
        ]
    
    def _mount_retries(self, session: requests.Session):
        """セッションにリトライ設定を追加"""
        retries = Retry(
            total=3,
            backoff_factor=1.2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
    
    def _get_random_delay(self, base_delay: float = 1.0) -> float:
        """ランダムな待機時間を生成（人間らしいアクセスパターンを模倣）"""
        # 参考サイトの基準: 30秒間に30ページ以下を目安
        # 1ページあたり最低1秒、最大3秒のランダム待機
        return random.uniform(base_delay * 0.8, base_delay * 2.5)
    
    def _rotate_user_agent(self):
        """User-Agentをランダムに切り替え"""
        new_ua = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': new_ua})
        print(f"User-Agentを切り替えました: {new_ua[:50]}...")
    
    def _refresh_session_if_needed(self):
        """必要に応じてセッションをリフレッシュ"""
        # 20リクエストごとにセッションをリフレッシュ
        if self.request_count > 0 and self.request_count % 20 == 0:
            print("セッションをリフレッシュしています...")
            self.session.close()
            self.session = requests.Session()
            self.session.headers.update(self.headers)
            self._rotate_user_agent()
            self._mount_retries(self.session)  # リトライ設定を再付与
            # セッションリフレッシュ時は少し長めに待機
            time.sleep(self._get_random_delay(2.0))
    
    def _fetch_work_top_soup(self, work_id: str):
        """作品トップページを取得して BeautifulSoup を返す"""
        self.request_count += 1
        self._refresh_session_if_needed()
        
        work_url = f"https://kakuyomu.jp/works/{work_id}"
        resp = self.session.get(work_url, timeout=(5, 20))
        resp.raise_for_status()
        return BeautifulSoup(resp.content, 'html.parser')

    def _extract_overview_title(self, soup: BeautifulSoup) -> str:
        """作品トップから概要タイトルを抽出"""
        try:
            # 1) WorkIntroductionBox 配下の EyeCatch_catchphrase（最も安定）
            node = soup.select_one('[class*="WorkIntroductionBox_catch"][class], [class*="WorkIntroductionBox_catch"] [class*="EyeCatch_catchphrase"]')
            if node and node.get_text(strip=True):
                return node.get_text(strip=True)

            # 2) ページ全体から EyeCatch_catchphrase を直接取得（前方一致/部分一致）
            node = soup.select_one('[class*="EyeCatch_catchphrase"]')
            if node and node.get_text(strip=True):
                return node.get_text(strip=True)

            # 2) 「概要」h2 見出し近傍から探索（フォールバック）
            h2 = soup.find('h2', string=re.compile(r'^\s*概要\s*$'))
            if h2:
                container = h2.find_parent()
                if container:
                    node2 = container.select_one('[class*="EyeCatch_catchphrase"]')
                    if node2 and node2.get_text(strip=True):
                        return node2.get_text(strip=True)
        except Exception:
            pass
        return ""

    def _extract_overview_description(self, soup: BeautifulSoup) -> str:
        """作品トップから概要本文を抽出（<br>は改行に変換）"""
        try:
            # 1) 折りたたみテキスト（クラスはハッシュ付きのため前方一致/部分一致）
            desc_div = soup.find('div', class_=re.compile(r"\bCollapseTextWithKakuyomuLinks_collapseText"))
            if not desc_div:
                # 2) 「概要」見出し近傍から探索（フォールバック）
                h2 = soup.find('h2', string=re.compile(r'^\s*概要\s*$'))
                if h2:
                    container = h2.find_parent()
                    if container:
                        desc_div = container.find('div', class_=re.compile(r"\bCollapseTextWithKakuyomuLinks_collapseText"))

            if desc_div:
                for br in desc_div.find_all('br'):
                    br.replace_with('\n')
                text = desc_div.get_text('\n', strip=True)
                return text
        except Exception:
            pass
        return ""
    
    def extract_novel_data(self, work_id: str, limit: Optional[int] = None) -> Optional[Dict]:
        """作品IDから統合JSONデータを抽出"""
        try:
            # エピソード一覧取得
            print(f"作品ID {work_id} のエピソード一覧を取得中...")
            # 作品トップから概要情報を取得（このSoupを一覧収集にも再利用して重複アクセスを回避）
            overview_title = ""
            overview_description = ""
            top_soup = None
            try:
                top_soup = self._fetch_work_top_soup(work_id)
                overview_title = self._extract_overview_title(top_soup)
                overview_description = self._extract_overview_description(top_soup)
            except Exception as e:
                print(f"警告: 概要情報の取得に失敗しました: {e}", file=sys.stderr)

            # 一覧取得に initial_soup を渡してトップの重複アクセスを避ける
            episodes_data = list_episodes_with_session(self.session, work_id, initial_soup=top_soup)
            total_episodes = len(episodes_data['episodes'])
            
            # エピソード数チェック
            if limit and limit > total_episodes:
                print(f"エラー: 指定されたエピソード数({limit})が総エピソード数({total_episodes})を超えています", file=sys.stderr)
                return None
            
            # 制限適用
            episodes = episodes_data['episodes']
            if limit:
                episodes = episodes[:limit]
                print(f"話数制限: {limit}話まで取得します")
            
            # スクレイピング処理
            scraped_episodes: List[Dict] = []
            removed_categories_aggregate: Dict[str, int] = {}
            for i, episode in enumerate(episodes, 1):
                print(f"[{i}/{len(episodes)}] エピソードを処理中: {episode['title']}")
                data = self.scrape_episode(episode['url'])
                if data:
                    # 作品本文のクリーニング（P1）
                    cleaned_text, removed_categories = self._clean_episode_text(data['content'])
                    for cat in removed_categories:
                        removed_categories_aggregate[cat] = removed_categories_aggregate.get(cat, 0) + 1
                    # TODO: Phase 2 - ここでメタデータを計算して追加
                    # text = data['content']
                    # length = len(text)
                    # dialogue_pattern = r'「[^」]*」'
                    # dialogue_matches = re.findall(dialogue_pattern, text)
                    # dialogue_ratio = sum(len(match) for match in dialogue_matches) / len(text) if len(text) > 0 else 0
                    # sentences = re.split(r'[。！？]', text)
                    # avg_sentence_length = sum(len(s) for s in sentences) / len(sentences) if len(sentences) > 0 else 0
                    scraped_episodes.append({
                        'number': i,
                        'title': data['episode_title'],
                        'url': episode['url'],
                        'text': cleaned_text,
                        'length': len(cleaned_text)
                        # TODO: Phase 2 - 以下を追加
                        # 'length': length,
                        # 'dialogue_ratio': dialogue_ratio,
                        # 'avg_sentence_length': avg_sentence_length
                    })
                else:
                    print(f"警告: エピソード {i} の取得に失敗しました")
                
                # ランダムな待機時間（参考サイトの基準に基づく）
                delay = self._get_random_delay(1.0)
                print(f"待機中... {delay:.1f}秒")
                time.sleep(delay)
            
            if not scraped_episodes:
                print("エラー: 取得できたエピソードがありません", file=sys.stderr)
                return None
            
            # analysis_scope.slices の生成（P1）
            analysis_scope = self._build_analysis_slices(scraped_episodes)

            # metrics の算出（任意/P1+）
            metrics = self._compute_metrics(scraped_episodes)

            # cleaning 情報（P1）
            cleaning = {
                'removed_boilerplates': bool(removed_categories_aggregate),
                'notes': [f"removed: {cat} ({cnt})" for cat, cnt in sorted(removed_categories_aggregate.items(), key=lambda x: (-x[1], x[0]))]
            }

            summary_title = (overview_title or '').strip()
            summary_description = (overview_description or '').strip()
            overview = {
                'title': summary_title,
                'description': summary_description,
                'length': len(summary_description)
            }

            # 統合JSONを構築
            result = {
                'title': data['title'] if scraped_episodes else 'Unknown',
                'author': data['author'] if scraped_episodes else 'Unknown',
                'work_url': f"https://kakuyomu.jp/works/{work_id}",
                'overview': overview,
                'total_episodes': total_episodes,
                'scraped_episodes': len(scraped_episodes),
                'episodes': scraped_episodes,
                'analysis_scope': analysis_scope,
                'cleaning': cleaning,
                'site': { 'name': 'kakuyomu' },
                'metrics': metrics
            }
            return result
            
        except Exception as e:
            print(f"エラー: 統合データの取得に失敗しました - {e}", file=sys.stderr)
            return None

    def _clean_episode_text(self, text: str) -> Tuple[str, List[str]]:
        """作品本文から評価依頼やSNS誘導などのボイラープレートを除去し、除去カテゴリを返す（P1）。

        単純な段落フィルタリングで安全側に。強ヒット（footer_heading 等）や複数ヒットで除去。
        """
        if not text:
            return text, []

        normalized = re.sub(r"\r\n?", "\n", text).strip()
        if not normalized:
            return "", []

        original_len = len(normalized)
        MIN_CHARS = 600
        MIN_RATIO = 0.6

        def perform_cleaning(strict: bool) -> Tuple[str, List[str]]:
            removed: List[str] = []
            cleaned_lines: List[str] = []
            lines = [ln for ln in re.split(r"\n+", normalized) if ln is not None]
            total = len(lines)
            for idx, ln in enumerate(lines):
                hit: List[str] = []
                for cat, pat in self._bp_patterns:
                    if pat.search(ln):
                        hit.append(cat)

                strong = any(cat in ("footer_heading",) for cat in hit)
                if strict:
                    is_edge = (idx < 3) or (total - idx <= 3)
                    should_remove = strong or (is_edge and hit) or (len(hit) >= 2)
                else:
                    should_remove = strong

                if should_remove:
                    removed.extend(hit if hit else ["misc"])
                    continue
                cleaned_lines.append(ln)

            cleaned_text = "\n\n".join(cleaned_lines).strip()
            cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
            return cleaned_text, sorted(set(removed))

        def is_sufficient(cleaned_text: str) -> bool:
            cleaned_len = len(cleaned_text)
            if cleaned_len == 0:
                return False
            if original_len >= MIN_CHARS and cleaned_len < MIN_CHARS:
                return False
            if cleaned_len < int(original_len * MIN_RATIO):
                return False
            return True

        strict_cleaned, strict_removed = perform_cleaning(strict=True)
        if is_sufficient(strict_cleaned):
            return strict_cleaned, strict_removed

        strong_cleaned, strong_removed = perform_cleaning(strict=False)
        if is_sufficient(strong_cleaned):
            return strong_cleaned, strong_removed

        fallback_text = re.sub(r"\n{3,}", "\n\n", normalized)
        return fallback_text, []

    def _build_analysis_slices(self, episodes: List[Dict]) -> Dict:
        """analysis_scope.slices を構築（P1）。
        目安: 各1800字。ep1=hook、中間=turning_point、最終=payoff。
        """
        n = len(episodes)
        if n == 0:
            return { 'episodes_included': [], 'slices': [] }

        TARGET_SIZE = 1800
        MIN_EP_LENGTH = 1500

        def normalize_text(value: str) -> str:
            if not value:
                return ''
            text = re.sub(r"\r\n?", "\n", value)
            text = re.sub(r"\n{3,}", "\n\n", text.strip())
            return text

        def get_episode_text(idx: int) -> str:
            if idx < 0 or idx >= n:
                return ''
            return normalize_text(episodes[idx].get('text', '') or '')

        def base_indices() -> List[int]:
            if n >= 10:
                indices = [0, 4, 9]
            else:
                mid = max(0, math.ceil(n / 2) - 1)
                indices = [0, mid, n - 1]
            while len(indices) < 3:
                indices.append(indices[-1])
            return indices[:3]

        def search_nearest(start_idx: int, avoid_used: bool, min_length: int) -> Optional[int]:
            offsets = [0]
            for step in range(1, n):
                offsets.extend([step, -step])

            best_idx = None
            best_len = -1
            for offset in offsets:
                candidate = start_idx + offset
                if candidate < 0 or candidate >= n:
                    continue
                if avoid_used and candidate in selected_indices:
                    continue
                text = get_episode_text(candidate)
                text_len = len(text)
                if text_len == 0:
                    continue
                if text_len >= min_length:
                    return candidate
                if text_len > best_len:
                    best_len = text_len
                    best_idx = candidate
            return best_idx

        def pick_episode(start_idx: int) -> int:
            attempts = [
                (True, MIN_EP_LENGTH),
                (False, MIN_EP_LENGTH),
                (False, 1),
            ]
            for avoid_used, min_len in attempts:
                candidate = search_nearest(start_idx, avoid_used=avoid_used, min_length=min_len)
                if candidate is not None:
                    return candidate
            return max(0, min(start_idx, n - 1))

        def extract_chunk(text: str, position: int) -> str:
            if not text:
                return ''
            if len(text) <= TARGET_SIZE:
                return text
            if position == 0:
                start = 0
            elif position == 1:
                mid = len(text) // 2
                start = max(0, min(mid - TARGET_SIZE // 2, len(text) - TARGET_SIZE))
            else:
                start = len(text) - TARGET_SIZE
            end = start + TARGET_SIZE
            return text[start:end]

        SLICE_MIN = 1500
        kinds_map = {0: 'hook', 1: 'turning_point', 2: 'payoff'}
        selected_indices: List[int] = []
        slices: List[Dict] = []
        episode_lengths = [len(get_episode_text(idx)) for idx in range(n)]
        sorted_by_length = sorted(range(n), key=lambda i: episode_lengths[i], reverse=True)

        def choose_fallback(original_idx: int, position: int) -> int:
            for idx in sorted_by_length:
                if idx == original_idx or idx in selected_indices:
                    continue
                if episode_lengths[idx] >= SLICE_MIN:
                    return idx
            for idx in sorted_by_length:
                if idx == original_idx:
                    continue
                if episode_lengths[idx] >= SLICE_MIN:
                    return idx
            for idx in sorted_by_length:
                if episode_lengths[idx] > 0:
                    return idx
            return original_idx

        for position, base_idx in enumerate(base_indices()):
            chosen_idx = pick_episode(base_idx)
            text = get_episode_text(chosen_idx)
            chunk = extract_chunk(text, position)

            if len(chunk) < SLICE_MIN:
                fallback_idx = choose_fallback(chosen_idx, position)
                if fallback_idx != chosen_idx:
                    chosen_idx = fallback_idx
                    text = get_episode_text(chosen_idx)
                    chunk = extract_chunk(text, position)

            if not chunk:
                fallback_idx = choose_fallback(chosen_idx, position)
                chosen_idx = fallback_idx
                text = get_episode_text(chosen_idx)
                chunk = extract_chunk(text, position)

            selected_indices.append(chosen_idx)
            ep_number = episodes[chosen_idx].get('number', chosen_idx + 1)
            slices.append({
                'ep': ep_number,
                'kind': kinds_map.get(position, 'slice'),
                'text': chunk
            })

        episodes_included: List[int] = []
        for idx in selected_indices:
            ep_number = episodes[idx].get('number', idx + 1)
            if ep_number not in episodes_included:
                episodes_included.append(ep_number)

        return { 'episodes_included': episodes_included, 'slices': slices }

    def _compute_metrics(self, episodes: List[Dict]) -> Dict:
        """軽量メトリクスを算出（任意/P1+）。"""
        texts = [ep.get('text', '') for ep in episodes if ep.get('text')]
        all_text = "\n\n".join(texts)
        total_chars = sum(len(t) for t in texts)
        n = len(texts)
        if total_chars == 0:
            return { 'total_chars': 0, 'avg_chars_per_episode': 0.0, 'dialogue_ratio': 0.0, 'unique_trigram_ratio': 0.0, 'mean_sentence_len': 0.0 }

        # 会話文割合
        dialogue_matches = re.findall(r'「[^」]*」', all_text)
        dialogue_len = sum(len(m) for m in dialogue_matches)
        dialogue_ratio = float(dialogue_len) / float(total_chars) if total_chars else 0.0

        # ユニーク3-gram率
        grams = [all_text[i:i+3] for i in range(max(0, total_chars - 2))]
        unique_trigram_ratio = (len(set(grams)) / len(grams)) if grams else 0.0

        # 平均文長
        sentences = re.split(r'[。！？!?]', all_text)
        sentence_lengths = [len(s) for s in sentences if s and s.strip()]
        mean_sentence_len = (sum(sentence_lengths) / len(sentence_lengths)) if sentence_lengths else 0.0

        return {
            'total_chars': total_chars,
            'avg_chars_per_episode': round(total_chars / n, 2) if n else 0.0,
            'dialogue_ratio': round(dialogue_ratio, 6),
            'unique_trigram_ratio': round(unique_trigram_ratio, 6),
            'mean_sentence_len': round(mean_sentence_len, 2)
        }
    
    def scrape_episode(self, url):
        """
        カクヨムのエピソードURLから情報を抽出
        """
        try:
            self.request_count += 1
            self._refresh_session_if_needed()
            
            response = self.session.get(url, timeout=(5, 20))
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # データ抽出
            data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'title': self._extract_title(soup),
                'author': self._extract_author(soup),
                'chapter': self._extract_chapter(soup),
                'episode_title': self._extract_episode_title(soup),
                'episode_number': self._extract_episode_number(soup),
                'content': self._extract_content(soup),
                'work_url': self._extract_work_url(url)
            }
            
            return data
            
        except requests.RequestException as e:
            print(f"リクエストエラー: {e}")
            return None
        except Exception as e:
            print(f"解析エラー: {e}")
            return None
    
    def _extract_title(self, soup):
        """作品タイトルを抽出"""
        # 1) 本文ヘッダの作品タイトル
        header_work_title = soup.select_one('#contentMain-header-workTitle')
        if header_work_title:
            text = header_work_title.get_text().strip()
            if text:
                return text

        # 2) パンくずの作品タイトル
        bc_work_title = soup.select_one('#worksEpisodesEpisodeHeader-breadcrumbs h1 a span')
        if bc_work_title:
            text = bc_work_title.get_text().strip()
            if text:
                return text

        # 3) ページ<title>から抽出（フォールバック）
        title_element = soup.find('title')
        if title_element:
            title_text = title_element.get_text()
            match = re.search(r'-\s*(.+?)\s*\(', title_text)
            if match:
                return match.group(1).strip()
        
        # 代替手段：リンク要素から抽出
        work_link = soup.find('a', href=re.compile(r'/works/\d+$'))
        if work_link:
            return work_link.get_text().strip()
        
        return "タイトル不明"
    
    def _extract_author(self, soup):
        """作者名を抽出"""
        # 1) ページ本文ヘッダの著者（安定）
        header_author = soup.select_one('#contentMain-header-author')
        if header_author:
            text = header_author.get_text().strip()
            if text:
                return text

        # 2) クラス/リンクパターン
        patterns = [
            ('span', {'class': re.compile(r'author|writer')}),
            ('a', {'href': re.compile(r'/users/')}),
        ]
        for tag, attrs in patterns:
            element = soup.find(tag, attrs)
            if element:
                author = element.get_text().strip()
                if author and len(author) < 100:
                    return author
        
        # ページタイトルから抽出
        title_element = soup.find('title')
        if title_element:
            title_text = title_element.get_text()
            match = re.search(r'\((.+?)\)', title_text)
            if match:
                return match.group(1).strip()
        
        return "作者不明"
    
    def _extract_chapter(self, soup):
        """章情報を抽出"""
        # 1) DOMから（例: <p class="chapterTitle"><span>第一章　…</span></p>）
        chapter_node = soup.select_one('p.chapterTitle span') or soup.select_one('p.chapterTitle')
        if chapter_node:
            text = chapter_node.get_text().strip()
            if text:
                return text

        # 2) テキストからパターン検索（全文を返す: 「第一章 …」含む）
        content_text = soup.get_text()
        chapter_patterns = [
            r'第[一二三四五六七八九十\d]+章[　\s]*[^\n]*',
            r'Chapter[　\s]*\d+[　\s]*[^\n]*',
            r'[第]?[0-9]+[章編部][　\s]*[^\n]*'
        ]
        for pattern in chapter_patterns:
            m = re.search(pattern, content_text)
            if m:
                return m.group(0).strip()

        return "章情報なし"
    
    def _extract_episode_title(self, soup):
        """エピソードタイトルを抽出"""
        # 1) DOMのエピソードタイトル
        epi = soup.select_one('p.widget-episodeTitle')
        if epi:
            text = epi.get_text().strip()
            if text:
                return text
        
        # 2) パンくずの h2 > span
        bc = soup.select_one('#worksEpisodesEpisodeHeader-breadcrumbs h2 span')
        if bc:
            text = bc.get_text().strip()
            if text:
                return text
        
        # 3) <title> からフォールバック
        title_element = soup.find('title')
        if title_element:
            title_text = title_element.get_text()
            match = re.match(r'(.+?) -', title_text)
            if match:
                return match.group(1).strip()
        
        return "エピソードタイトル不明"
    
    def _extract_episode_number(self, soup):
        """話数を抽出"""
        episode_title = self._extract_episode_title(soup)
        
        # 話数のパターンを検索
        patterns = [
            r'第(\d+)話',
            r'第([一二三四五六七八九十]+)話',
            r'(\d+)話',
            r'Episode[　\s]*(\d+)',
            r'Ep\.?[　\s]*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, episode_title)
            if match:
                num_str = match.group(1)
                # 漢数字を数字に変換
                if num_str.isdigit():
                    return int(num_str)
                else:
                    return self._kanji_to_number(num_str)
        
        return 0
    
    def _extract_content(self, soup):
        """本文を抽出（純粋な小説本文のみ）"""
        # 小説本文のコンテナを特定
        content_div = soup.find('div', class_='widget-episodeBody')
        if not content_div:
            return ""
        
        # 小説本文のみを抽出（<p>タグのみを対象）
        paragraphs = content_div.find_all('p')
        
        content_lines = []
        for p in paragraphs:
            # blankクラスを持つ要素は除外（空行用）
            if p.get('class') and 'blank' in p.get('class'):
                continue
                
            text = p.get_text(strip=True)
            
            # 空行や不要な要素を除外
            if text and text not in ['', '　', ' ', '\n']:
                # 不要な要素のキーワードチェック
                unwanted_keywords = [
                    '応援しよう', 'ハートをクリック', '人が応援しました', 
                    '応援コメント', '応援したユーザー', '閉じる', 
                    '表示設定', '目次', '前のエピソード', 'カクヨム',
                    '作者を応援', 'ログインが必要', '応援する', '応援コメント',
                    'ビューワー設定', '新規登録で充実', '切実なおねがい'
                ]
                
                # 不要なキーワードが含まれていないかチェック
                if not any(keyword in text for keyword in unwanted_keywords):
                    content_lines.append(text)
        
        # 段落を結合（空行で区切り）
        content = '\n\n'.join(content_lines)
        
        # 余分な空白や改行を整理
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # 連続する空行を2行に統一
        content = re.sub(r' +', ' ', content)  # 連続するスペースを1つに
        
        return content
    
    # TODO: Phase 2 - メタデータ追加機能
    # 生成AIの評価向上のため、以下のメタデータを各エピソードに追加予定：
    # - length: 文字数
    # - dialogue_ratio: 会話文の割合（「」で囲まれた部分）
    # - avg_sentence_length: 平均文長
    # 
    # 実装予定箇所: extract_novel_data()メソッド内で各エピソードのtext抽出後に計算
    # 計算ロジック:
    #   length = len(text)
    #   dialogue_pattern = r'「[^」]*」'
    #   dialogue_matches = re.findall(dialogue_pattern, text)
    #   dialogue_ratio = sum(len(match) for match in dialogue_matches) / len(text)
    #   sentences = re.split(r'[。！？]', text)
    #   avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
    
    def _extract_work_url(self, episode_url):
        """エピソードURLから作品URLを抽出"""
        match = re.match(r'(https://kakuyomu\.jp/works/\d+)', episode_url)
        return match.group(1) if match else ""
    
    def _kanji_to_number(self, kanji_str):
        """漢数字を数字に変換（改良版）"""
        if isinstance(kanji_str, int):
            return kanji_str
            
        # 数字がすでに含まれている場合はそのまま返す
        if re.search(r'\d', str(kanji_str)):
            match = re.search(r'\d+', str(kanji_str))
            if match:
                return int(match.group())
        
        kanji_dict = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '１': 1, '２': 2, '３': 3, '４': 4, '５': 5,
            '６': 6, '７': 7, '８': 8, '９': 9
        }
        
        kanji_str = str(kanji_str).strip()
        
        # 単純な一文字の場合
        if len(kanji_str) == 1 and kanji_str in kanji_dict:
            return kanji_dict[kanji_str]
        
        # 十の処理
        if kanji_str == '十':
            return 10
        elif kanji_str.startswith('十'):
            if len(kanji_str) == 2:
                return 10 + kanji_dict.get(kanji_str[1], 0)
        elif kanji_str.endswith('十'):
            if len(kanji_str) == 2:
                return kanji_dict.get(kanji_str[0], 1) * 10
        elif '十' in kanji_str:
            parts = kanji_str.split('十')
            if len(parts) == 2:
                tens = kanji_dict.get(parts[0], 1) if parts[0] else 1
                ones = kanji_dict.get(parts[1], 0) if parts[1] else 0
                return tens * 10 + ones
        
        # フォールバック：最初に見つかった数字を返す
        for char in kanji_str:
            if char in kanji_dict:
                return kanji_dict[char]
        
        return 1  # デフォルト値
    

def print_novel_summary(data: dict) -> None:
    """統合JSONのサマリーを表示"""
    print("\n=== 取得結果 ===")
    print(f"作品タイトル: {data['title']}")
    print(f"作者: {data['author']}")
    overview = data.get('overview')
    if overview and (overview.get('title') or overview.get('description')):
        print("[概要]")
        if overview.get('title'):
            print(f"  タイトル: {overview['title']}")
        if overview.get('description'):
            desc = overview['description']
            preview = desc if len(desc) <= 200 else desc[:200] + '…'
            print(f"  説明: {preview}")
        if overview.get('length') is not None:
            print(f"  文字数: {overview['length']}")
    print(f"総エピソード数: {data['total_episodes']}")
    print(f"取得エピソード数: {data['scraped_episodes']}")
    print(f"作品URL: {data['work_url']}")
    print(f"エピソード一覧:")
    for episode in data['episodes']:
        print(f"  {episode['number']}. {episode['title']}")


def main():
    """メイン実行関数"""
    # 引数解析
    if len(sys.argv) < 2:
        print("エラー: 作品IDが必要です", file=sys.stderr)
        print("使用方法: python kakuyomu_scraper.py {小説ID} [話数制限]", file=sys.stderr)
        return
    
    work_id = sys.argv[1]
    limit = None
    
    if len(sys.argv) >= 3:
        try:
            limit = int(sys.argv[2])
            if limit <= 0:
                print("エラー: エピソード数は1以上である必要があります", file=sys.stderr)
                return
        except ValueError:
            print("エラー: エピソード数は数値である必要があります", file=sys.stderr)
            return
    
    # 統合JSON出力
    scraper = KakuyomuScraper()
    data = scraper.extract_novel_data(work_id, limit)
    
    if data:
        print_novel_summary(data)
        save_novel_json(data, work_id)
    else:
        print("統合JSONの生成に失敗しました", file=sys.stderr)
        return

if __name__ == "__main__":
    main()