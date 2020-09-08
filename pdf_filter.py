"""aggressive-ish pdf cleaning script for language models.
    Based off: https://gist.github.com/leogao2/8d4662dfb8e58e8c58ef94df5d46413d by Leo Gao"""

import os
import re
import fix_unicode


def listdir(x):
    return [x + '/' + fn for fn in os.listdir(x)]


def id(x):
    return x


def average_word_length(text):
    """
    get average word length of a given text file

    :param txt: string
    :return: float of avg word length
    """
    n_words = len(text.split())
    n_chars = len(text)
    avgw = n_chars / (n_words + 1)
    return avgw


def mean(x):
    x = list(x)
    if not x: return 0
    return sum(x) / len(x)


def nonzero(x):
    return filter(id, x)


def is_letter(x):
    return x in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def all_equal(x):
    return all([n == x[0] for n in x])


def replace_hyphenated(text):
    return re.sub(r'-\n(\w+ *)', r'\1\n', text)


def remove_leading_and_trailing_nums(text):
    # remove leading and trailing numbers (i.e page nums)
    text = text.strip()
    text = re.sub(r'^(\d+)', '', text)
    text = re.sub(r'(\d+)$', '', text)
    return text.strip()


def cid_percentage(text):
    """
    detects the amount of cid numbers (an artefact from missing custom fonts) found in a converted pdf.
    Example:

        "which maintained contacts not least in  the  South  East  Asian  extreme  right.  To  some  extent  during  the
        (cid:38)(cid:82)(cid:79)(cid:71)(cid:3) (cid:58)(cid:68)(cid:85)(cid:15)"

    :param text: string
    :return: float between 0 and 1 representing density of cid nos in string
    """
    n_matches = len(re.findall('\(cid:[0-9]+\)', text))
    if text:
        return (n_matches * 8) / len(text)
    else: return 0.


def remove_cid(text):
    return text.replace('\(cid:[0-9]+\)', '')


def filter_double_whitespace(text):
    return re.sub("\s\s+" , " ", text)

def filter_newlines(text):
    return re.sub("\n", " ", text)

def pdf_filter(text):
    cid_perc = cid_percentage(text)
    # if cid_perc is larger than threshold, it's probably a latex / alt font heavy document. delete the whole thing.
    if cid_perc > .03:
        print('ERROR: too many font errors - skipping document.')
        return ""
    # if mean line len is too short, it's probably garbled, not useful, or overly latex-y
    whole_doc_mean_line_len = mean(nonzero(map(len, text.split('\n'))))
    if whole_doc_mean_line_len < 15:
        print('ERROR: avg mean line length too short - skipping document.')
        return ""
    word_length = average_word_length(text)
    # if average word length is too big or small, document is not worth keeping
    if word_length > 45:
        print('ERROR: avg word length too large - skipping document.')
        return ""
    elif word_length < 2:
        print('ERROR: avg word length too short - skipping document.')
        return ""
    paras = text.split('\n\n')
    out = []
    for para in paras:

        # replace hyphens at end of line, filter out new lines in the middle of paragraphs,
        # and remove double whitespaces
        para = replace_hyphenated(para)
        para = filter_newlines(para)
        para = filter_double_whitespace(para)

        # if mean line len is too short, it's probably garbled or not useful
        mean_line_len = mean(nonzero(map(len, para.split('\n'))))
        if mean_line_len < 2.:
            continue

        # if cid_percentage is higher than 10%, it's likely a latex heavy para and won't make sense without it
        # delete the whole para
        if cid_percentage(para) > .1:
            continue
        # not enough letters (i.e math, tables, etc)
        letterness = mean(map(is_letter, para))
        if letterness < 0.40:
            continue

        #   final cleaning steps:
        #   remove leading and trailing numbers (usually pagenos)
        #   remove any remaining cid strings
        #   fix any unicode / ligature related errors
        para = fix_unicode.fix_unicode(remove_cid(remove_leading_and_trailing_nums(para)))
        if para != '':
            # only append if not empty
            out.append(para)

        # remove empty strings from prev step
        for i in out:
            if not i:
                out.remove(i)

    return '\n\n'.join(out)