#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
syosetu_scraper.py
小説家になろう小説スクレイピングツール
小説家になろうの小説作品から統合JSONを出力します

使用方法:
    python scraper.py {小説ID} [話数制限]

例:
    python scraper.py n2596la
    python scraper.py n2596la 5

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
from scrapers.syosetu.list_episodes import list_episodes_with_session

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

class SyosetuScraper:
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
        # クリーニング用の正規表現パターン（小説家になろう用）
        self._bp_patterns: List[Tuple[str, re.Pattern]] = [
            ("stars_request", re.compile(r"[★☆]{1,}|★で称える|評価(お願いします|ください)|レビュー(を|お願いします)")),
            ("like_request", re.compile(r"♡|ハート|いいね|応援(しよう|お願いします|して|のお願い)")),
            ("sns_promo", re.compile(r"SNS|Twitter|X\s*\(|フォロー|宣伝|読了報告")),
            ("ranking", re.compile(r"(月間|週間|年間).{0,8}(ランキング|順位)|1位|上位|目標")),
            ("thanks_request", re.compile(r"お礼とお願い|お願い|ギフト|切実")),
            ("update_notice", re.compile(r"更新告知|次回更新|告知|予告")),
            ("footer_heading", re.compile(r"^\s*[★☆]{4,}.*[★☆]{4,}\s*$")),
            ("author_note", re.compile(r"作者のコメント|あとがき|作者より|お疲れ様でした")),
            ("copyright_notice", re.compile(r"当サイトの内容、テキスト、画像等の無断転載・無断使用を固く禁じます|Unauthorized copying and replication of the contents of this site, text and images are strictly prohibited")),
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
        return random.uniform(base_delay * 0.8, base_delay * 2.5)
    
    def _rotate_user_agent(self):
        """User-Agentをランダムに切り替え"""
        new_ua = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': new_ua})
        print(f"User-Agentを切り替えました: {new_ua[:50]}...")
    
    def _refresh_session_if_needed(self):
        """必要に応じてセッションをリフレッシュ"""
        if self.request_count > 0 and self.request_count % 20 == 0:
            print("セッションをリフレッシュしています...")
            self.session.close()
            self.session = requests.Session()
            self.session.headers.update(self.headers)
            self._rotate_user_agent()
            self._mount_retries(self.session)
            time.sleep(self._get_random_delay(2.0))
    
    def _fetch_work_top_soup(self, work_id: str):
        """作品トップページを取得して BeautifulSoup を返す"""
        self.request_count += 1
        self._refresh_session_if_needed()
        
        work_url = f"https://ncode.syosetu.com/{work_id}/"
        resp = self.session.get(work_url, timeout=(5, 20))
        resp.raise_for_status()
        return BeautifulSoup(resp.content, 'html.parser')

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """作品タイトルを抽出"""
        try:
            # 1) ページタイトルから抽出
            title_element = soup.find('title')
            if title_element:
                title_text = title_element.get_text()
                # 「作品名 - 作者名 - 小説家になろう」の形式から抽出
                match = re.search(r'^(.+?)\s*-\s*(.+?)\s*-\s*小説家になろう', title_text)
                if match:
                    return match.group(1).strip()
            
            # 2) 作品名の見出しから抽出
            title_h1 = soup.find('h1')
            if title_h1:
                text = title_h1.get_text(strip=True)
                if text and text != "小説家になろう":
                    return text
                    
        except Exception:
            pass
        return "タイトル不明"

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """作者名を抽出"""
        try:
            # 1) 作者関連のdivから抽出（「作者：」の形式）
            author_divs = soup.find_all('div', class_=re.compile(r'writer|author'))
            for div in author_divs:
                text = div.get_text(strip=True)
                if '作者：' in text:
                    # 「作者：海城あおの」から「海城あおの」を抽出
                    match = re.search(r'作者：(.+)', text)
                    if match:
                        return match.group(1).strip()
            
            # 2) 作者名のdivから抽出（小説家になろうの標準構造）
            author_div = soup.find('div', class_='novel_writername')
            if author_div:
                author_link = author_div.find('a')
                if author_link:
                    text = author_link.get_text(strip=True)
                    if text:
                        return text
            
            # 3) ページタイトルから抽出
            title_element = soup.find('title')
            if title_element:
                title_text = title_element.get_text()
                match = re.search(r'^(.+?)\s*-\s*(.+?)\s*-\s*小説家になろう', title_text)
                if match:
                    return match.group(2).strip()
            
            # 4) 作者名のリンクから抽出（フォールバック）
            author_link = soup.find('a', href=re.compile(r'/user/\d+'))
            if author_link:
                text = author_link.get_text(strip=True)
                if text:
                    return text
                    
        except Exception:
            pass
        return "作者不明"

    def _extract_overview_title(self, soup: BeautifulSoup) -> str:
        """作品概要タイトルを抽出"""
        try:
            # 小説家になろうでは「あらすじ」セクションを探す
            synopsis_heading = soup.find('h2', string=re.compile(r'あらすじ'))
            if synopsis_heading:
                return "あらすじ"
            
            # フォールバック: 概要関連の見出しを探す
            overview_headings = soup.find_all(['h2', 'h3'], string=re.compile(r'概要|あらすじ|作品紹介'))
            if overview_headings:
                return overview_headings[0].get_text(strip=True)
                
        except Exception:
            pass
        return ""

    def _extract_overview_description(self, soup: BeautifulSoup) -> str:
        """作品概要説明を抽出"""
        try:
            # 1) 小説家になろうの標準構造：novel_ex IDから抽出（最優先）
            description_div = soup.find('div', id='novel_ex')
            if description_div:
                print(f"DEBUG: novel_ex IDで見つかりました")
                print(f"DEBUG: 元のテキスト長: {len(description_div.get_text())}")
                # より安全な方法でテキストを取得
                # まずHTMLを文字列として取得し、<br>タグを改行に置換
                html_content = str(description_div)
                html_content = html_content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                # HTMLタグを除去
                import re
                text = re.sub(r'<[^>]+>', '', html_content)
                text = text.strip()
                print(f"DEBUG: 変換後テキスト長: {len(text)}")
                print(f"DEBUG: テキスト内容: {repr(text[:200])}")
                if text:
                    return text
            
            # 1.5) より広範囲な検索：あらすじテキストを含むdivを探す
            all_divs = soup.find_all('div')
            for div in all_divs:
                div_text = div.get_text()
                if '最悪な状況' in div_text and 'ハーレムあり' in div_text:
                    print(f"DEBUG: あらすじを含むdivを発見")
                    print(f"DEBUG: 元のテキスト長: {len(div_text)}")
                    # <br>タグを改行に変換
                    for br in div.find_all('br'):
                        br.replace_with('\n')
                    text = div.get_text('\n', strip=True)
                    print(f"DEBUG: 変換後テキスト長: {len(text)}")
                    print(f"DEBUG: テキスト内容: {repr(text[:200])}")
                    if text:
                        return text
            
            # 2) novel_exクラスから抽出
            description_div = soup.find('div', class_='novel_ex')
            if description_div:
                # <br>タグを改行に変換
                for br in description_div.find_all('br'):
                    br.replace_with('\n')
                text = description_div.get_text('\n', strip=True)
                if text:
                    return text
            
            # 3) あらすじ関連のdivから抽出（デバッグで見つかった要素）
            desc_divs = soup.find_all('div', class_=re.compile(r'novel_ex|description|synopsis|story|summary'))
            for div in desc_divs:
                # <br>タグを改行に変換
                for br in div.find_all('br'):
                    br.replace_with('\n')
                text = div.get_text('\n', strip=True)
                if text and len(text) > 20:  # 十分な長さがある場合のみ
                    return text
            
            # 4) あらすじセクションを探す（フォールバック）
            synopsis_heading = soup.find('h2', string=re.compile(r'あらすじ'))
            if synopsis_heading:
                # 次の要素から概要を取得
                next_element = synopsis_heading.find_next_sibling()
                if next_element:
                    # <br>タグを改行に変換
                    for br in next_element.find_all('br'):
                        br.replace_with('\n')
                    text = next_element.get_text('\n', strip=True)
                    return text
            
            # 5) 概要関連の見出しの次の要素を探す
            overview_headings = soup.find_all(['h2', 'h3'], string=re.compile(r'概要|あらすじ|作品紹介'))
            for heading in overview_headings:
                next_element = heading.find_next_sibling()
                if next_element:
                    for br in next_element.find_all('br'):
                        br.replace_with('\n')
                    text = next_element.get_text('\n', strip=True)
                    if text and len(text) > 10:  # 十分な長さがある場合のみ
                        return text
                        
        except Exception:
            pass
        return ""


    def scrape_episode(self, episode_url: str) -> Optional[Dict]:
        """エピソードページから本文を取得"""
        try:
            self.request_count += 1
            self._refresh_session_if_needed()
            
            response = self.session.get(episode_url, timeout=(5, 20))
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # エピソードタイトルを抽出
            episode_title = self._extract_episode_title(soup)
            
            # エピソード本文を抽出
            content = self._extract_episode_content(soup)
            
            if not content:
                print(f"警告: エピソードの本文が取得できませんでした: {episode_url}")
                return None
            
            # 本文をクリーニング
            cleaned_content, removed_categories = self._clean_episode_text(content)
            
            return {
                'episode_title': episode_title,
                'content': cleaned_content,
                'url': episode_url,
                'scraped_at': datetime.now().isoformat(),
                'removed_categories': removed_categories
            }
            
        except Exception as e:
            print(f"エピソード取得でエラー: {e}")
            return None

    def _extract_episode_title(self, soup: BeautifulSoup) -> str:
        """エピソードタイトルを抽出"""
        try:
            # ページタイトルから抽出
            title_element = soup.find('title')
            if title_element:
                title_text = title_element.get_text()
                # 「作品名 - エピソードタイトル」の形式から抽出
                if ' - ' in title_text:
                    parts = title_text.split(' - ')
                    if len(parts) >= 2:
                        return parts[-1].strip()
            
            # フォールバック：h1タグから抽出
            h1 = soup.find('h1')
            if h1:
                return h1.get_text(strip=True)
                
        except Exception:
            pass
        return "エピソードタイトル不明"

    def _extract_episode_content(self, soup: BeautifulSoup) -> str:
        """エピソード本文を抽出（novel_honbun優先、改行保持）"""

        def normalize_node(node) -> str:
            try:
                for br in node.find_all('br'):
                    br.replace_with('\n')
            except AttributeError:
                pass
            text = node.get_text('\n', strip=True)
            text = text.replace('\u00a0', ' ')
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text

        def is_usable(text: str) -> bool:
            if not text:
                return False
            # 明らかなナビゲーション要素は除外
            unwanted_tokens = ['ブックマーク', '感想を書く', 'ログイン', '設定', 'しおりを挟む']
            score = sum(1 for token in unwanted_tokens if token in text)
            if score >= 3:
                return False
            return len(text) >= 200

        try:
            primary = soup.find('div', id='novel_honbun')
            if primary:
                text = normalize_node(primary)
                if is_usable(text):
                    return text

            candidates = [
                ('div', {'id': re.compile(r'novel_honbun', re.I)}),
                ('div', {'class': re.compile(r'(novel|honbun|text|body)', re.I)}),
                ('section', {'class': re.compile(r'(novel|honbun|text|body)', re.I)}),
            ]

            best_text = ''
            for tag, attrs in candidates:
                nodes = soup.find_all(tag, attrs=attrs)
                for node in nodes:
                    text = normalize_node(node)
                    if not text:
                        continue
                    if len(text) > len(best_text):
                        best_text = text
            return best_text
        except Exception:
            return ""

    def _clean_episode_text(self, text: str) -> Tuple[str, List[str]]:
        """エピソード本文からノイズを除去し、除去カテゴリを返す"""
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

                strong = any(cat in ("footer_heading", "copyright_notice") for cat in hit)
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
        """analysis_scope.slices を構築。
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
                (True, MIN_EP_LENGTH),      # 1. 未使用で十分な長さ
                (False, MIN_EP_LENGTH),     # 2. 重複許容だが十分な長さ
                (False, 1),                 # 3. 最長のもの
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
            # 1) 未使用かつ十分な長さ
            for idx in sorted_by_length:
                if idx == original_idx or idx in selected_indices:
                    continue
                if episode_lengths[idx] >= SLICE_MIN:
                    return idx
            # 2) 既使用でも十分な長さ
            for idx in sorted_by_length:
                if idx == original_idx:
                    continue
                if episode_lengths[idx] >= SLICE_MIN:
                    return idx
            # 3) 最長（既使用含む）
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
        """軽量メトリクスを算出。"""
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

    def extract_novel_data(self, work_id: str, limit: Optional[int] = None) -> Optional[Dict]:
        """作品IDから統合JSONデータを抽出（エピソード本文も含む）"""
        try:
            print(f"作品ID {work_id} の基本情報を取得中...", flush=True)
            
            # 作品トップページを取得
            top_soup = self._fetch_work_top_soup(work_id)
            
            
            # 基本情報を抽出
            title = self._extract_title(top_soup)
            author = self._extract_author(top_soup)
            overview_title = self._extract_overview_title(top_soup)
            overview_description = self._extract_overview_description(top_soup)
            
            # エピソード一覧を取得（モジュールを使用）
            episodes_data = list_episodes_with_session(self.session, work_id, initial_soup=top_soup)
            episodes = episodes_data['episodes']
            total_episodes = len(episodes)
            
            
            print(f"基本情報取得完了:")
            print(f"  タイトル: {title}")
            print(f"  作者: {author}")
            print(f"  総エピソード数: {total_episodes}")
            clean_overview_title = (overview_title or '').strip()
            clean_overview_desc = (overview_description or '').strip()
            if clean_overview_title:
                print(f"  概要タイトル: {clean_overview_title}")
            print(f"  概要説明: {clean_overview_desc[:100]}..." if clean_overview_desc else "  概要説明: なし")
            
            # エピソード数チェック
            if limit and limit > total_episodes:
                print(f"エラー: 指定されたエピソード数({limit})が総エピソード数({total_episodes})を超えています", file=sys.stderr)
                return None
            
            # 制限適用
            if limit:
                episodes = episodes[:limit]
                print(f"話数制限: {limit}話まで取得します")
            
            # エピソード本文を取得
            scraped_episodes: List[Dict] = []
            removed_categories_aggregate: Dict[str, int] = {}
            
            for i, episode in enumerate(episodes, 1):
                print(f"[{i}/{len(episodes)}] エピソードを処理中: {episode['title']}")
                episode_data = self.scrape_episode(episode['url'])
                if episode_data:
                    # 除去されたカテゴリを集計
                    for cat in episode_data.get('removed_categories', []):
                        removed_categories_aggregate[cat] = removed_categories_aggregate.get(cat, 0) + 1
                    
                    scraped_episodes.append({
                        'number': i,
                        'title': episode_data['episode_title'],
                        'url': episode['url'],
                        'text': episode_data['content'],
                        'length': len(episode_data['content'])
                    })
                else:
                    print(f"警告: エピソード {i} の取得に失敗しました")
                
                # ランダムな待機時間
                delay = self._get_random_delay(1.0)
                print(f"待機中... {delay:.1f}秒")
                time.sleep(delay)
            
            if not scraped_episodes:
                print("エラー: 取得できたエピソードがありません", file=sys.stderr)
                return None
            
            # analysis_scope の生成
            analysis_scope = self._build_analysis_slices(scraped_episodes)

            # metrics の算出
            metrics = self._compute_metrics(scraped_episodes)

            summary_title = (overview_title or '').strip()
            summary_description = (overview_description or '').strip()
            overview = {
                'title': summary_title,
                'description': summary_description,
                'length': len(summary_description)
            }

            # 統合JSONを構築
            result = {
                'title': title,
                'author': author,
                'work_url': f"https://ncode.syosetu.com/{work_id}/",
                'overview': overview,
                'total_episodes': total_episodes,
                'scraped_episodes': len(scraped_episodes),
                'episodes': scraped_episodes,
                'analysis_scope': analysis_scope,
                'cleaning': {
                    'removed_boilerplates': bool(removed_categories_aggregate),
                    'notes': [f"removed: {cat} ({cnt})" for cat, cnt in sorted(removed_categories_aggregate.items(), key=lambda x: (-x[1], x[0]))]
                },
                'site': {'name': 'syosetu'},
                'metrics': metrics
            }
            return result
            
        except Exception as e:
            print(f"エラー: 統合データの取得に失敗しました - {e}", file=sys.stderr)
            return None

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
    print(f"サイト: {data['site']['name']}")

def main():
    """メイン実行関数"""
    # 引数解析
    if len(sys.argv) < 2:
        print("エラー: 作品IDが必要です", file=sys.stderr)
        print("使用方法: python scraper.py {小説ID} [話数制限]", file=sys.stderr)
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
    scraper = SyosetuScraper()
    data = scraper.extract_novel_data(work_id, limit)
    
    if data:
        print_novel_summary(data)
        save_novel_json(data, work_id)
    else:
        print("統合JSONの生成に失敗しました", file=sys.stderr)
        return

if __name__ == "__main__":
    main()
