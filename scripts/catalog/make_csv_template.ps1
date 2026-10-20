# scripts/catalog/make_csv_template.ps1  (run from the repo root)
if (-not (Test-Path catalog_seed/images)) {
    New-Item -ItemType Directory -Path catalog_seed/images -Force | Out-Null
    Write-Host "Created catalog_seed/images folder. Add your .jpg garment photos there, then rerun this script."
    exit 0
}

$rows = Get-ChildItem catalog_seed/images -Filter *.jpg | Sort-Object Name | ForEach-Object {
  [pscustomobject]@{
    id=$_.BaseName;
    title="";
    brand="Own";
    price="";
    gender="";
    category="";
    sub_category="";
    primary_color="";
    pattern="";
    formality="";
    ethnic_wear="";
    tryon_suitable="";
    sizes="";
    image="images/$($_.Name)"
  }
}

if ($rows.Count -eq 0) {
    Write-Host "No .jpg images found in catalog_seed/images. Please photograph 15-20 garments and place them in catalog_seed/images first."
    exit 0
}

$rows | Export-Csv catalog_seed/catalog.csv -NoTypeInformation -Encoding utf8
"$($rows.Count) rows written to catalog_seed/catalog.csv; fill the blank columns in Excel or your editor."
