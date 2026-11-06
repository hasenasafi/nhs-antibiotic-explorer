import requests

url = "https://opendata.nhsbsa.net/api/3/action/datastore_search_sql"

sql = """
SELECT
    YEAR_MONTH,
    REGIONAL_OFFICE_NAME,
    BNF_CHEMICAL_SUBSTANCE,
    SUM(ITEMS) AS total_items,
    SUM(NIC) AS total_nic
FROM `EPD_SNOMED_202608`
WHERE BNF_CHEMICAL_SUBSTANCE_CODE LIKE '0501%'
GROUP BY YEAR_MONTH, REGIONAL_OFFICE_NAME, BNF_CHEMICAL_SUBSTANCE
ORDER BY total_items DESC
"""

params = {"resource_id": "EPD_SNOMED_202608", "sql": sql}

response = requests.get(url, params=params, timeout=120)
print("Status code:", response.status_code)

data = response.json()
records = data["result"]["result"]["records"]
print("Number of rows:", len(records))

print("\nTop 5 rows:")
for row in records[:5]:
   print(row["REGIONAL_OFFICE_NAME"], "|", row["BNF_CHEMICAL_SUBSTANCE"], "|", row["total_items"], "items", "|", f"£{row['total_nic']:,.2f}")