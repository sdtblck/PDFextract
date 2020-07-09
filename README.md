# PDFextract
Extracting pdfs using pdfminer.six and pyPDF2

# Setup
pip install -r requirements.txt

# Usage
python pdf_extract.py

the above will default to parsing all pdfs in 'samples' and outputting to 'output'. 
Pass a path to a folder containing pdfs with --path_to_folder & change output folder with --out_path args

E.G
python pdf_extract.py --path_to_folder /Users/user/my_pdfs --out_path /Users/documents/parsed_pdfs

By default, PDFs are split into single page documents before parsing the text, this is faster for large PDFs. Turn this option off with -ns or --no_split arg

