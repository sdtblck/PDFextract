# PDFextract
Extracting text from pdfs using pdfminer.six and pyPDF2

# Setup
pip install -r requirements.txt

# Usage
`python pdf_extract.py`

the above will default to parsing all pdfs in 'samples' and save output txt files to 'output'. 
Pass a path to a folder containing pdfs with --path_to_folder & change output folder with --out_path args

E.G
`python pdf_extract.py --path_to_folder /Users/user/my_pdfs --out_path /Users/documents/parsed_pdfs`

## Full usage details:
```
usage: pdf_extract.py [-h] [--path_to_folder PATH_TO_FOLDER]
                      [--out_path OUT_PATH] [--filter]

CLI for PDFextract - extracts plaintext from PDF files

optional arguments:
  -h, --help            show this help message and exit
  --path_to_folder PATH_TO_FOLDER
                        Path to folder containing pdfs
  --out_path OUT_PATH   Output location for final .txt file
  --filter              whether to clean & filter resulting txt files
```

