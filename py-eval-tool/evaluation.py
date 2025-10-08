#!/usr/bin/env python3

import sys
import json
import io
from scrapers.syosetu.scraper import SyosetuScraper
from eval import run_evaluation
import asyncio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def main():
    # Get command line arguments
    args = sys.argv[1:]
    
    # Validate arguments
    if len(args) < 4:
        result = {
            "success": False,
            "message": "Missing required parameters: source, workId, and AI model",
        }
        print(json.dumps(result, indent=2))
        return 1
    
    agent = args[0]
    work_id = args[1]
    episodes = int(args[2]) if len(args) > 2 and args[2].isdigit() else 1
    stage_num = args[3]

    eval_result = asyncio.run(run_evaluation(agent, work_id, episodes, stage_num))
    result = {
        "success": True,
        "message": "evaluation completed",
        "data": eval_result,
        "workId": work_id,
        "episodes": episodes,
    }

    print("###JSON-BEGIN###")
    print(json.dumps(result, indent=2))
    print("###JSON-END###")

    return 0

if __name__ == "__main__":
    sys.exit(main())
