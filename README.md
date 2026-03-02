# Catalog Compare

A desktop application to compare two product catalogs (CSV files) and identify added, removed, and changed products. Export results as a PDF report.

## Features

- Load two CSV files (old and new catalog)
- Auto-detect column mapping (barcode, cost, product name)
- Identify added, removed, and price-changed products
- View results in a tabbed interface with summary cards
- Export a detailed PDF comparison report

## Download

Pre-built binaries are available on the [Releases](https://github.com/thomaszim/catalog-compare/releases) page:

- **macOS**: `Catalog-Compare-macOS.zip`
- **Windows**: `Catalog Compare.exe`

## Build from source

### Requirements

- Python 3.10+

### macOS

```bash
git clone https://github.com/thomaszim/catalog-compare.git
cd catalog-compare
chmod +x build.sh
./build.sh
```

The `.app` bundle will be in the `dist/` folder.

### Windows

```bash
git clone https://github.com/thomaszim/catalog-compare.git
cd catalog-compare
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name "Catalog Compare" --collect-all fpdf2 run.py
```

The `.exe` will be in the `dist\` folder.

### Run without building

```bash
pip install fpdf2
python run.py
```

## Usage

1. **Load CSVs**: Select your old and new catalog CSV files
2. **Map columns**: Verify or adjust the auto-detected column mapping (barcode, cost, product name)
3. **Compare**: Review added, removed, and changed products in the results tabs
4. **Export**: Save the comparison as a PDF report

## License

[MIT](LICENSE)
