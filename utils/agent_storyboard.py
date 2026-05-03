import json
import os
import sys

def generate_storyboard(session_id):
    json_path = f"reports/sessions/{session_id}.json"
    if not os.path.exists(json_path):
        print(f"Session {session_id} not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    markdown = [
        f"# Visual Agent Storyboard: {session_id}",
        f"**Started**: {data.get('start_time')}",
        f"**Steps Conducted**: {data.get('current_step')}",
        "---",
        "## Agent Logic & Interaction Flow",
        ""
    ]

    for entry in data.get("history", []):
        status_emoji = "✅" if entry["result"] == "Success" else "❌"
        markdown.append(f"### Step {entry['step']}: {entry['action']} {status_emoji}")
        markdown.append(f"- **Result**: {entry['result']}")
        markdown.append(f"- **Timestamp**: {entry['timestamp']}")
        if entry.get("screenshot"):
            markdown.append(f"![Step {entry['step']} Screenshot](../../reports/{entry['screenshot']})")
        markdown.append("")

    report_path = f"reports/storyboard_{session_id}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines([line + "\n" for line in markdown])
    
    print(f"Storyboard Report Generated: {report_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_storyboard(sys.argv[1])
    else:
        # Find latest session
        sessions_dir = "reports/sessions"
        if os.path.exists(sessions_dir):
            files = sorted(os.listdir(sessions_dir), reverse=True)
            if files:
                generate_storyboard(files[0].replace(".json", ""))
