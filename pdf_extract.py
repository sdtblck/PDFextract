import os
import glob
from PyPDF2 import PdfFileWriter, PdfFileReader
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import BytesIO
from pdfminer.pdfparser import PDFSyntaxError
from PyPDF2.utils import PdfReadError
import argparse
import tqdm

# ---------------------------------------------------------------------------
# Split:


def splitter(path, save=True):
    """
    Splits multi-page PDF files into multiple individual pages.

    :param path: path to pdf
    # TODO: :param save: if True, saves split pdfs to split/*.pdf, else returns split PDFs as list
    :return:
    """
    # remove all old splits
    splits = glob.glob('split/*.pdf')
    for split_pdf in splits:
        os.remove(split_pdf)

    #split each page & save to separate file
    pdf = PdfFileReader(path)
    for page in range(pdf.getNumPages()):
        try:
            pdf_writer = PdfFileWriter()
            pdf_writer.addPage(pdf.getPage(page))

            output_filename = 'split/{}.pdf'.format(page + 1)

            with open(output_filename, 'wb') as out:
                pdf_writer.write(out)

        except PdfReadError as e:
            print(f'Read failed for page {page}')
            print(e)

# ---------------------------------------------------------------------------
# Extract:


def pdf_to_text(path):
    """
    Extracts text from a (preferably single page) pdf file

    :param path:
    :return:
    """
    manager = PDFResourceManager()
    retstr = BytesIO()
    layout = LAParams(all_texts=True)
    device = TextConverter(manager, retstr, laparams=layout)
    filepath = open(path, 'rb')
    interpreter = PDFPageInterpreter(manager, device)
    try:
        for page in PDFPage.get_pages(filepath, check_extractable=True):
            interpreter.process_page(page)
    except PDFSyntaxError as e:
        print(f'ERROR: Extraction failed for {path} \n {e}')

    text = retstr.getvalue()
    filepath.close()
    device.close()
    retstr.close()
    return text


def extract_main(out_name="Output", path_to_pdfs='split'):
    all_pdfs = glob.glob(f"{path_to_pdfs}/*.pdf")
    all_pdfs.sort()

    for pdf_file in all_pdfs:
        text_output = pdf_to_text(pdf_file)  # Extract text with PDF_to_text Function call
        text1_output = text_output.decode("utf-8")  # Decode result from bytes to text
        # Save extracted text to file
        with open(f"output/{out_name}.txt", "a", encoding="utf-8") as text_file:
            text_file.writelines(text1_output)

if __name__ == "__main__":

    #TODO: parallelize with mp
    #      filtering / cleaning functions

    parser = argparse.ArgumentParser(description='CLI for PDFextract - extracts plaintext from PDF files')
    parser.add_argument('--path_to_folder', help='Path to folder containing pdfs', required=False, default='samples')
    parser.add_argument('--out_path', help='Output location for final .txt file', required=False, default='output')
    parser.add_argument('-ns', '--no_split', action='store_false', help='if present, do *NOT* split the pdf file into single pages before parsing')
    args = parser.parse_args()

    path_to_folder = args.path_to_folder
    all_pdfs = glob.glob(f"{path_to_folder}/**/*.pdf", recursive=True)

    # make outdir
    try:
        os.makedirs(args.out_path)
    except FileExistsError:
        print('Outdir already exists')

    for pdf in tqdm.tqdm(all_pdfs, total=len(all_pdfs)):
        fname = os.path.split(pdf)[1][:-4]
        if args.no_split:
            splitter(pdf)
            path_to_folder = 'split'
        extract_main(fname, path_to_folder)