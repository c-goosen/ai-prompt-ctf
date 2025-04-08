

def format_msg_history(msg_history: list)->list:
    return [
        {"content":x.get("memory",""),"role": x.get("metadata", {}).get("role")}
        for x in msg_history
    ]
