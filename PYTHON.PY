


from tavily import TavilyClient

# ============================================================
# TAVILY API KEY
# ============================================================

API_KEY = "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"



tavily = TavilyClient(api_key=API_KEY)

url = "https://scholarships.gov.in/public/schemeGuidelines/Top_Class_Education_Scheme_2018.pdf"

response = tavily.extract(url)

print("\nSCHOLARSHIP DOCUMENT")
print("=" * 80)

for result in response["results"]:
    print("\nTITLE:", result["title"])
    print("URL:", result["url"])
    print("\nCONTENT:")
    print(result["raw_content"])

print("\n" + "=" * 80)
print("EXTRACTION COMPLETED")