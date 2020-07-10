from PyPDF2 import PdfFileWriter, PdfFileReader
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import BytesIO
from pdfminer.pdfparser import PDFSyntaxError
from PyPDF2.utils import PdfReadError
from multiprocessing import Pool, cpu_count
from itertools import repeat
import argparse, tqdm, re, glob, os

# ---------------------------------------------------------------------------
# Split:


def splitter(path):
    """
    Splits multi-page PDF files into multiple individual pages.

    :param path: path to pdf
    :return:
    """
    # remove all old splits
    splits = glob.glob('split/*.pdf')
    for split_pdf in splits:
        os.remove(split_pdf)

    #split each page & save to separate file
    pdf = PdfFileReader(path)
    try:
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
    except PdfReadError as e:
        print(f'Read failed for path {path}')
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

def extract_text_wrapper(pdf_file, out_name="Output", out_path="output"):
    text_output = pdf_to_text(pdf_file)  # Extract text with PDF_to_text Function call
    text1_output = text_output.decode("utf-8")  # Decode result from bytes to text
    # Save extracted text to file
    with open(f"{out_path}/{out_name}.txt", "a", encoding="utf-8") as text_file:
        text_file.writelines(text1_output)

def extract_main_mp(out_name="Output", path_to_pdfs='split', out_path="output"):
    all_pdfs = glob.glob(f"{path_to_pdfs}/*.pdf")

    # sorts filenames by numerical value
    all_pdfs.sort(key=lambda f: int(re.sub('\D', '', f)))

    # populate list of out names
    out_names = []
    for n in range(len(all_pdfs)):
        out = f"{out_name}_{n:06}"
        out_names.append(out)

    # init pool with as many CPUs as available
    cpu_no = cpu_count() - 1
    p = Pool(cpu_no)
    p.starmap(extract_text_wrapper, zip(all_pdfs, out_names, repeat(out_path)))
    with open(f"{out_path}/{out_name}.txt", 'w') as outfile:
        for fname in out_names:
            with open(f"{out_path}/{fname}.txt") as infile:
                outfile.write(infile.read())
    for fname in out_names:
        os.remove(f"{out_path}/{fname}.txt")



if __name__ == "__main__":
    #TODO: filtering / cleaning functions

    parser = argparse.ArgumentParser(description='CLI for PDFextract - extracts plaintext from PDF files')
    parser.add_argument('--path_to_folder', help='Path to folder containing pdfs', required=False, default='samples')
    parser.add_argument('--out_path', help='Output location for final .txt file', required=False, default='output')
    args = parser.parse_args()

    path_to_folder = args.path_to_folder
    all_pdfs = glob.glob(f"{path_to_folder}/**/*.pdf", recursive=True)

    # make outdir
    try:
        os.makedirs(args.out_path)
    except FileExistsError:
        print('Outdir already exists')

    try:
        os.makedirs('split')
    except FileExistsError:
        print('splitdir already exists')

    for pdf in tqdm.tqdm(all_pdfs, total=len(all_pdfs)):
        fname = os.path.split(pdf)[1][:-4]
        splitter(pdf)
        path_to_folder = 'split'
        extract_main_mp(fname, path_to_folder, args.out_path)
