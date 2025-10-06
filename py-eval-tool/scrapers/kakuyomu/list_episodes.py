#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
list_episodes.py
作品IDからカクヨム作品トップを取得し、全エピソードURLを列挙します。

使用例:
    python list_episodes.py 16818792439429953221
    python list_episodes.py 16818792439429953221 --json > episodes.json

出力:
    既定ではURLを1行ずつ標準出力へ。--json でJSONを出力。
"""

import argparse
import sys
import re
import time
import random
from urllib.parse import urljoin
from typing import List, Dict
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://kakuyomu.jp/"


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    })
    # リトライ設定を追加
    retries = Retry(
        total=3,
        backoff_factor=1.2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def build_work_url(work_id: str) -> str:
    work_id = str(work_id).strip()
    return urljoin(BASE_URL, f"works/{work_id}")


def extract_episodes_from_soup(soup: BeautifulSoup, work_id: str) -> List[Dict[str, str]]:
    """作品トップのHTMLから、該当作品のエピソードリンクを抽出する。

    返却: [{"episode_id", "url", "title"}]
    """
    pattern = re.compile(rf"^/works/{re.escape(work_id)}/episodes/\d+$")

    found: List[Dict[str, str]] = []
    seen = set()

    for a in soup.find_all('a', href=pattern):
        href = a.get('href', '').strip()
        if not href or href in seen:
            continue
        seen.add(href)

        full_url = urljoin(BASE_URL, href)
        m = re.search(r"/episodes/(\d+)$", href)
        episode_id = m.group(1) if m else ''
        title = a.get_text(strip=True)

        found.append({
            'episode_id': episode_id,
            'url': full_url,
            'title': title,
        })

    return found


def follow_pagination_and_collect(session: requests.Session, work_url: str, work_id: str, initial_soup: BeautifulSoup | None = None) -> List[Dict[str, str]]:
    """作品トップのページネーションを辿りつつ全エピソードURLを収集する。
    rel="next" または クエリ付きの次ページリンク（例: ?page=2）に対応。
    """
    all_items: List[Dict[str, str]] = []
    seen_urls = set()

    next_url = work_url
    page_count = 0
    use_initial = initial_soup is not None
    
    while next_url:
        if next_url in seen_urls:
            print(f"デバッグ: 既に処理済みのURLに到達しました: {next_url}", file=sys.stderr)
            break
        seen_urls.add(next_url)
        page_count += 1

        print(f"デバッグ: ページ {page_count} を処理中: {next_url}", file=sys.stderr)
        if use_initial:
            soup = initial_soup  # 先頭1回目のみ外部から受領したSoupを使用
            use_initial = False
        else:
            resp = session.get(next_url, timeout=(5, 20))
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            # 一覧ページ取得後にランダム待機
            delay = random.uniform(1.0, 2.5)
            print(f"デバッグ: 次ページまで待機 {delay:.1f}s", file=sys.stderr)
            time.sleep(delay)

        items = extract_episodes_from_soup(soup, work_id)
        print(f"デバッグ: このページで {len(items)} 個のエピソードを発見", file=sys.stderr)
        
        # 掲載順を保ったまま重複排除
        existing = {item['url'] for item in all_items}
        new_items = 0
        for item in items:
            if item['url'] not in existing:
                all_items.append(item)
                existing.add(item['url'])
                new_items += 1
        
        print(f"デバッグ: 新規追加: {new_items} 個、累計: {len(all_items)} 個", file=sys.stderr)

        # 次ページ探索（rel="next" 優先）
        next_link = soup.find('link', rel='next')
        if next_link and next_link.get('href'):
            next_url = urljoin(next_url, next_link['href'])
            print(f"デバッグ: rel='next' で次ページを発見: {next_url}", file=sys.stderr)
            continue

        # フォールバック: 次ページらしきa要素
        a_next = soup.find('a', attrs={'rel': 'next'}) or soup.find('a', string=re.compile(r'次|Next', re.I))
        if a_next and a_next.get('href'):
            next_url = urljoin(next_url, a_next['href'])
            print(f"デバッグ: a要素で次ページを発見: {next_url}", file=sys.stderr)
        else:
            # より積極的な次ページ検索
            page_links = soup.find_all('a', href=re.compile(r'[?&]page=\d+'))
            if page_links:
                # 最大のページ番号を探す
                max_page = 0
                for link in page_links:
                    href = link.get('href', '')
                    match = re.search(r'[?&]page=(\d+)', href)
                    if match:
                        page_num = int(match.group(1))
                        max_page = max(max_page, page_num)
                
                if max_page > page_count:
                    next_url = f"{work_url}?page={page_count + 1}"
                    print(f"デバッグ: クエリパラメータで次ページを発見: {next_url}", file=sys.stderr)
                else:
                    next_url = None
                    print(f"デバッグ: これ以上のページが見つかりませんでした", file=sys.stderr)
            else:
                next_url = None
                print(f"デバッグ: 次ページリンクが見つかりませんでした", file=sys.stderr)

    print(f"デバッグ: 全 {page_count} ページを処理し、合計 {len(all_items)} 個のエピソードを収集", file=sys.stderr)
    return all_items


def list_episodes_with_session(session: requests.Session, work_id: str, initial_soup: BeautifulSoup | None = None) -> Dict:
    """外部セッションおよび初回ページのBeautifulSoupを受け取り、一覧を収集して返す。"""
    work_url = build_work_url(work_id)

    episodes = follow_pagination_and_collect(session, work_url, work_id, initial_soup=initial_soup)

    result = {
        'work_id': work_id,
        'work_url': work_url,
        'scraped_at': datetime.now().isoformat(),
        'episode_count': len(episodes),
        'episodes': episodes,
    }
    return result


def list_episodes(work_id: str) -> Dict:
    session = create_session()
    work_url = build_work_url(work_id)

    episodes = follow_pagination_and_collect(session, work_url, work_id)

    result = {
        'work_id': work_id,
        'work_url': work_url,
        'scraped_at': datetime.now().isoformat(),
        'episode_count': len(episodes),
        'episodes': episodes,
    }
    return result


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description='カクヨム作品のエピソードURL一覧を出力します')
    parser.add_argument('work_id', help='作品ID (例: 16818792439429953221)')
    parser.add_argument('--json', action='store_true', help='JSONで出力する（既定はURLを改行区切り）')
    args = parser.parse_args(argv)

    try:
        data = list_episodes(args.work_id)
        if args.json:
            import json
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for ep in data['episodes']:
                print(ep['url'])
        return 0
    except requests.RequestException as e:
        print(f"HTTPエラー: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"処理エラー: {e}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))


