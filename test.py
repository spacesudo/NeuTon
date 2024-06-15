import re
def extract_ca(url: str):
    pattern = r"track-([a-zA-Z0-9]+)"
    
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    else: 
        return None
    
    
print(extract_ca("ttdhdhdhgdgdtrack-hdhdhdhdhdhd"))  
