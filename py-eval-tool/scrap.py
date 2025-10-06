#!/usr/bin/env python3

import sys
import json
import io
from scrapers.syosetu.scraper import SyosetuScraper
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def main():
    # Get command line arguments
    args = sys.argv[1:]
    
    # Validate arguments
    if len(args) < 2:
        result = {
            "success": False,
            "message": "Missing required parameters: source and workId",
        }
        print(json.dumps(result, indent=2))
        return 1
    
    source = args[0]
    workId = args[1]
    episodes = int(args[2]) if len(args) > 2 and args[2].isdigit() else None

    data = {}
    if source == 'syosetu':
        syosetu_scraper = SyosetuScraper()
        data = syosetu_scraper.extract_novel_data(workId, episodes)
    
    result = {
        "success": True,
        "message": "scrap completed",
        "data": {
            **data,
            'work_id': workId
        },
        "source": source,
        "workId": workId,
        "episodes": episodes,
    }

    output_path = Path(f"input/{workId}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("###JSON-BEGIN###")
    print(json.dumps(result, indent=2))
    print("###JSON-END###")

    return 0

if __name__ == "__main__":
    sys.exit(main())
