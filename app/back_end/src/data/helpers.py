import csv

# ----------------
# Helper functions
# ----------------

def construct_clinvar_gene_identifiers_url(gene: str, max: int = 10000) -> str:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    query = f"?db=clinvar&term={gene}[gene]&retmax={max}"
    return f"{base_url}{query}"

def contruct_clinvar_summaries_url(identifiers: list[str]) -> str:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    query = f"?db=clinvar&rettype=vcv&is_variationid&id={','.join(identifiers)}&from_esearch=true"
    return f"{base_url}{query}"

def write_to_csv(columns, rows, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)