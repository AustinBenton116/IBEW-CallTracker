import requests
import json  
import re
from bs4 import BeautifulSoup

def run_scraper():
    print("Running Version 4.3 hard-numeric phone exclusion engine...")
    url = "https://where2bro.com/where-to-go/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')

        all_locals = []
        current_local = None

        for p in paragraphs:
            text = p.get_text().strip()
            if not text:
                continue
            
            text_upper = text.upper()

            has_phone_number = bool(re.search(r'\(\d{3}\)\s*\d{3}[-–—\s]*\d{4}', text))
            starts_properly = text_upper.startswith("LU") or (text and text[0].isdigit())
            is_invalid_header = any(w in text_upper for w in ["JOBLINE", "WELCOME TO", "BOOK", "H&W", "OFFICE", "ZONE"]) or len(text) >= 70
            is_header = has_phone_number and starts_properly and not is_invalid_header
            
            if is_header:
                if current_local:
                    all_locals.append(current_local)
                
                state_match = re.search(r'\b([A-Z]{2})\b', text_upper)
                detected_state = state_match.group(1) if state_match else "Unknown"

                current_local = {
                    "union_name": text,
                    "state": detected_state,
                    "wage_values_seen": set(),
                    "wage_scales": [],
                    "status_info": "",
                    "highest_wage": 0.0,
                    "call_count": 0,
                    "has_work": False
                }
                continue

            if not current_local:
                continue

            is_wage_keyword = any(w in text_upper for w in ["SCALE", "COMMERICAL", "COMMERCIAL", "INDUSTRIAL", "RESIDENTIAL", "ZONE"])
            has_money_sign = "$" in text
            is_benefit = any(b in text_upper for b in ["PENSION", "H&W", "HEALTH", "WELFARE", "VACATION", "VAC", "ANNUITY", "401K", "401(K)"])
            
            raw_digits = re.sub(r'\D', '', text)
            contains_hidden_phone = len(raw_digits) >= 7 and not (len(raw_digits) == 7 and "." in text)

            if (is_wage_keyword or has_money_sign or text.startswith("$")) and not is_benefit and not contains_hidden_phone:
                clean_scale = text_upper.replace("SCALE", "").replace("SCALES", "")
                for char in ["=", "-", "–", "—", ":", "$", "*"]:
                    clean_scale = clean_scale.replace(char, "")
                
                clean_scale = " ".join(clean_scale.split()).strip()
                wage_numbers = re.findall(r'\d+\.\d+|\d+', clean_scale)
                if wage_numbers:
                    found_wage = max([float(w) for w in wage_numbers])
                    if 15.0 < found_wage < 120.0 and len(text) < 85:
                        if found_wage not in current_local["wage_values_seen"]:
                            current_local["wage_values_seen"].add(found_wage)
                            label = text.split('=')[0].split('–')[0].split('-')[0].replace('SCALE', '').replace('*', '').strip()
                            if label == text or (any(char.isdigit() for char in label) and len(label) < 3): 
                                label = ""
                            display_val = f"${found_wage:.2f} ({label})".replace(" ()", "").strip()
                            current_local["wage_scales"].append(display_val)
                            if found_wage > current_local["highest_wage"]:
                                current_local["highest_wage"] = found_wage
                        continue

            if is_benefit or "JOBLINE" in text_upper:
                continue

            if "JOB CALLS" in text_upper or "AVAILABLE FOR" in text_upper:
                if not current_local["status_info"]:
                    current_local["status_info"] = text.split(".")[0].strip() + "."
                    current_local["has_work"] = True
                    count_match = re.search(r'^(\d+)\b', text)
                    if count_match:
                        current_local["call_count"] = int(count_match.group(1))
                continue

            if text_upper.startswith("WORK ") or text_upper.startswith("LOCAL "):
                clean_paragraph = " ".join(text.split())
                first_sentence = clean_paragraph.split(".")[0].strip() + "."
                first_sentence_upper = first_sentence.upper()
                if len(first_sentence) < 75 and ":" not in first_sentence and not any(bad in first_sentence_upper for bad in ["MILLION", "BILLION", "PEORIA", "GALESBURG", "QUINCY"]):
                    if not current_local["status_info"]:
                        current_local["status_info"] = first_sentence
                        if any(w in first_sentence_upper for w in ["GOOD", "STEADY", "PICKING UP", "BUSY"]):
                            current_local["has_work"] = True

        if current_local:
            all_locals.append(current_local)

        for local in all_locals:
            if not local["status_info"]:
                local["status_info"] = "No explicit job details listed."
            if local["wage_scales"]:
                cleaned_labels = [w.replace(" ()", "").strip() for w in local["wage_scales"]]
                local["wage_scale_display"] = "\n".join(cleaned_labels)
            else:
                local["wage_scale_display"] = "N/A"
            del local["wage_scales"]
            del local["wage_values_seen"]

        with open("jobs_data.json", "w") as f:
            json.dump({"locals": all_locals}, f, indent=4)
        print(f"Extraction successful! Total Records: {len(all_locals)}")

if __name__ == "__main__":
    run_scraper()