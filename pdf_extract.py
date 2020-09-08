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
import argparse, tqdm, re, glob, os, istarmap
from pdf_filter import pdf_filter
import traceback
import shutil

# ---------------------------------------------------------------------------
# Split:

def splitter_mp(pdf_obj, page_num):
    try:
        pdf_writer = PdfFileWriter()
        pdf_writer.addPage(pdf_obj.getPage(page_num))

        output_filename = '.tmp/{}.pdf'.format(page_num + 1)

        with open(output_filename, 'wb') as out:
            pdf_writer.write(out)

    except PdfReadError:
        print(f'Read failed for page {page_num}')
        traceback.print_exc()


def splitter(p, path):
    """
    Splits multi-page PDF files into multiple individual pages.

    :param path: path to pdf
    :return:
    """
    # remove all old splits
    splits = glob.glob('.tmp/*.pdf')
    for split_pdf in splits:
        os.remove(split_pdf)

    # split each page & save to separate file
    try:
        pdf = PdfFileReader(path)
        for _ in tqdm.tqdm(p.istarmap(splitter_mp, zip(repeat(pdf), range(pdf.getNumPages()))), total = pdf.getNumPages(),
                           desc="splitting", leave=False):
            pass
    except PdfReadError:
        print(f'Read failed for path {path}')
        traceback.print_exc()
    return "done"


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
    except (PDFSyntaxError, TypeError):
        print(f'ERROR: Extraction failed for {path}')
        traceback.print_exc()

    text = retstr.getvalue()
    filepath.close()
    device.close()
    retstr.close()
    return text


def extract_text_wrapper(pdf_file, out_name="Output", out_path=".tmp"):
    text_output = pdf_to_text(pdf_file)  # Extract text with PDF_to_text Function call
    text1_output = text_output.decode("utf-8")  # Decode result from bytes to text
    # Save extracted text to file
    with open(f"{out_path}/{out_name}.txt", "a", encoding="utf-8") as text_file:
        text_file.writelines(text1_output)


def extract_main_mp(p, out_name="Output", path_to_pdfs='.tmp', out_path="output", no_filter=False):
    all_pdfs = glob.glob(f"{path_to_pdfs}/*.pdf")

    # sorts filenames by numerical value
    all_pdfs.sort(key=lambda f: int(re.sub('\D', '', f)))

    # populate list of out names
    out_names = []
    for n in range(len(all_pdfs)):
        out = f"{out_name}_{n:06}"
        out_names.append(out)

    # Extract text from PDFS
    for _ in tqdm.tqdm(p.istarmap(extract_text_wrapper, zip(all_pdfs, out_names, repeat(".tmp"))),
                       total=len(all_pdfs), desc='pages', leave=False):
        pass

    # merge text files
    outfile_preclean = ""
    for fname in out_names:
        with open(f".tmp/{fname}.txt") as infile:
            outfile_preclean += infile.read()

    outfile_postclean = outfile_preclean if no_filter else pdf_filter(outfile_preclean, fn=out_name)

    if outfile_postclean.strip():
        with open(f"{out_path}/{out_name}.txt", 'w') as outfile:
            outfile.write(outfile_postclean)

    for fname in out_names:
        os.remove(f".tmp/{fname}.txt")
    return "done"


# ---------------------------------------------------------------------------
# Utils:

def timeout(func, args=(), kwargs={}, timeout_duration=1, default=None):
    import signal

    class TimeoutError(Exception):
        pass

    def handler(signum, frame):
        raise TimeoutError()

    # set the timeout handler
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_duration)
    try:
        result = func(*args, **kwargs)
    except TimeoutError as exc:
        result = default
    finally:
        signal.alarm(0)

    return result


def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024.0 or unit == 'PiB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def get_size_per_page(path):
    """
    gets the average size per page of a PDF document.
    :param path: path to pdf
    :return: size in bytes per page
    """
    try:
        num_pages = PdfFileReader(path).getNumPages()
        file_size = os.path.getsize(path)
        return file_size / num_pages
    except PdfReadError:
        print(f'Read failed for path {path}')
        traceback.print_exc()
        return None



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CLI for PDFextract - extracts plaintext from PDF files')
    parser.add_argument('--path_to_folder', help='Path to folder containing pdfs', required=False, default='samples')
    parser.add_argument('--out_path', help='Output location for final .txt file', required=False, default='output')
    parser.add_argument('-nf', '--no_filter', help="turn off cleaning & filtering resulting txt files", action='store_true')
    parser.add_argument('--size', help="Do not process files larger than this size per page in bytes "
                                       "(mostly images) - default 300000", type=int, default=300000)

    args = parser.parse_args()

    path_to_folder = args.path_to_folder
    all_pdfs = glob.glob(f"{path_to_folder}/**/*.pdf", recursive=True)

    # init pool with as many CPUs as available
    cpu_no = cpu_count() - 1
    p = Pool(cpu_no)

    # make outdir
    try:
        os.makedirs(args.out_path, exist_ok=True)
    except FileExistsError:
        print('Outdir already exists')

    try:
        os.makedirs('.tmp', exist_ok=True)
    except FileExistsError:
        print('.tmp dir already exists')

    for pdf in tqdm.tqdm(all_pdfs, total=len(all_pdfs), desc='books'):
        sz = timeout(get_size_per_page, args=(pdf,), timeout_duration=240)
        if sz is not None:
            # if filesize per page is larger than a certain amount,
            # the document is probably image-heavy and not worth parsing
            if sz > args.size:
                print(f'file size per page for {pdf} over cutoff of {human_readable_size(args.size)}: {human_readable_size(sz)}')
                continue
        fname = os.path.split(pdf)[1][:-4]
        x = timeout(splitter, args=(p, pdf), timeout_duration=240)
        if x is not None:
            x = timeout(extract_main_mp, args=(p, fname, ".tmp", args.out_path, args.no_filter), timeout_duration=240)
        if x is None:
            print(f'Timeout error for {fname}')
    shutil.rmtree(".tmp")
