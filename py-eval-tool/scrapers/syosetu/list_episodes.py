#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
list_episodes.py
小説家になろうのエピソード一覧取得モジュール
作品ページからエピソード一覧を抽出します
"""

import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

def list_episodes(work_id: str) -> Dict:
    """
    作品IDからエピソード一覧を取得
    
    Args:
        work_id: 作品ID (例: "n2596la")
    
    Returns:
        Dict: エピソード一覧の辞書
            {
                'episodes': [
                    {
                        'number': 1,
                        'title': 'エピソードタイトル',
                        'url': 'https://ncode.syosetu.com/...'
                    },
                    ...
                ]
            }
    """
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import random
    
    # セッション設定
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # リトライ設定
    retries = Retry(
        total=3,
        backoff_factor=1.2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    try:
        # 作品トップページを取得
        work_url = f"https://ncode.syosetu.com/{work_id}/"
        response = session.get(work_url, timeout=(5, 20))
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # エピソード一覧を抽出
        episodes = _extract_episode_list(soup)
        
        return {
            'episodes': episodes
        }
        
    except Exception as e:
        print(f"エピソード一覧取得でエラー: {e}")
        return {'episodes': []}
    finally:
        session.close()

def list_episodes_with_session(session, work_id: str, initial_soup: Optional[BeautifulSoup] = None) -> Dict:
    """
    既存のセッションを使用してエピソード一覧を取得
    
    Args:
        session: requests.Session オブジェクト
        work_id: 作品ID (例: "n2596la")
        initial_soup: 既に取得済みのBeautifulSoupオブジェクト（省略可）
    
    Returns:
        Dict: エピソード一覧の辞書
    """
    try:
        if initial_soup:
            # 既に取得済みのSoupを使用
            soup = initial_soup
        else:
            # 作品トップページを取得
            work_url = f"https://ncode.syosetu.com/{work_id}/"
            response = session.get(work_url, timeout=(5, 20))
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        
        # エピソード一覧を抽出
        episodes = _extract_episode_list(soup)
        
        return {
            'episodes': episodes
        }
        
    except Exception as e:
        print(f"エピソード一覧取得でエラー: {e}")
        return {'episodes': []}

def _extract_episode_list(soup: BeautifulSoup) -> List[Dict]:
    """エピソード一覧を抽出"""
    episodes = []
    try:
        # 小説家になろうのエピソード一覧を探す
        # 目次セクション（novelindex）を探す
        index_div = soup.find('div', class_='novelindex')
        if index_div:
            # 目次内のエピソードリンクを取得
            episode_links = index_div.find_all('a', href=re.compile(r'/\d+/$'))
        else:
            # フォールバック：ページ全体からエピソードリンクを探す
            episode_links = soup.find_all('a', href=re.compile(r'/\d+/$'))
        
        for i, link in enumerate(episode_links, 1):
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # 感想ページやその他の不要なリンクを除外
            # また、作者のマイページやその他の不要なリンクも除外
            exclude_patterns = ['impression', 'review', 'comment', 'mypage', 'user']
            if (href and title and 
                not any(exclude in href for exclude in exclude_patterns) and
                href.startswith('/') and  # 相対URLのみ
                re.match(r'/[^/]+/\d+/$', href) and  # エピソード番号のパターン
                not title in ['感想', 'レビュー', '海城あおの']):  # 特定の不要なタイトルを除外
                
                # 相対URLを絶対URLに変換
                episode_url = urljoin("https://ncode.syosetu.com/", href)
                episodes.append({
                    'number': i,
                    'title': title,
                    'url': episode_url
                })
                
    except Exception as e:
        print(f"エピソード一覧の取得でエラー: {e}")
        
    return episodes

if __name__ == "__main__":
    # テスト用
    import sys
    if len(sys.argv) >= 2:
        work_id = sys.argv[1]
        result = list_episodes(work_id)
        print(f"取得したエピソード数: {len(result['episodes'])}")
        for i, episode in enumerate(result['episodes'][:3]):
            print(f"  {i+1}. {episode['title']} -> {episode['url']}")
    else:
        print("使用方法: python list_episodes.py {作品ID}")
