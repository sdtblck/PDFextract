"""aggressive-ish pdf cleaning script for language models.
    Based off: https://gist.github.com/leogao2/8d4662dfb8e58e8c58ef94df5d46413d by Leo Gao"""

import os
import re
import fix_unicode

lone_accent_dict = {"a´": "á", "e´": "é", "i´": "í", "o´": "ó", "u´": "ú",
                    "a¨": "ä", "e¨": "ë", "i¨": "ï", "o¨": "ö", "u¨": "ü",
                    "a^": "â", "e^": "ê", "i^": "î", "o^": "ô", "u^": "û",
                    "a`": "à", "e`": "è", "i`": "ì", "o`": "ò", "u`": "ù",
                    "a~": "ã", "o~": "õ", "n~": "ñ"}

lone_accent_dict.update({k.upper(): v.upper() for k, v in lone_accent_dict.items()})


def ditch_combining_diacritics(text):
    for orig, repl in lone_accent_dict.items():
        text = text.replace(orig, repl)
    text = re.sub(r'[\u0300-\u036F]', '', text)
    return re.sub(r'(?:\xa8|[\u02C0-\u02DF])', '', text)


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

def is_date(x):
    res = re.match(r'.*([1-3][0-9]{3})', x)
    if res is not None:
        return True
    else:
        return False


def header_footer_filter(para):
    """if para is short & begins with ©, r {date}, copyright {date}, remove para"""
    if len(para) < 50:
        if para.strip()[0] == "©":
            return ""
        elif para.strip()[0] == "r":
            second_word = para.strip().split(" ")[1]
            if is_date(second_word):
                return ""
        elif para.strip().split(" ")[0] == "copyright":
            second_word = para.strip().split(" ")[1]
            if is_date(second_word):
                return ""
    return para


def all_equal(x):
    return all([n == x[0] for n in x])


def replace_hyphenated(text):
    text = re.sub(r'-[?\s]\n{1,2}(\w+ *)', r'\1\n', text)
    return re.sub(r'-\s{1,2}(\w+ *)', r'\1', text)


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
    return re.sub('\(cid:[0-9]+\)', '', text)


def filter_double_whitespace(text):
    return re.sub("\s\s+" , " ", text)


def filter_newlines(text):
    return re.sub("\n", " ", text)


def pdf_filter(text, fn):
    cid_perc = cid_percentage(text)
    # if cid_perc is larger than threshold, it's probably a latex / alt font heavy document. delete the whole thing.
    if cid_perc > .03:
        print('ERROR: too many font errors - skipping {}.'.format(fn))
        return ""
    # if mean line len is too short, it's probably garbled, not useful, or overly latex-y
    whole_doc_mean_line_len = mean(nonzero(map(len, text.split('\n'))))
    if whole_doc_mean_line_len < 15:
        print('ERROR: avg mean line length too short - skipping {}.'.format(fn))
        return ""
    word_length = average_word_length(text)
    # if average word length is too big or small, document is not worth keeping
    if word_length > 45:
        print('ERROR: avg word length too large - skipping {}.'.format(fn))
        return ""
    elif word_length < 2:
        print('ERROR: avg word length too short - skipping {}.'.format(fn))
        return ""
    # replace hyphens at end of lines and paragraphs
    text = replace_hyphenated(text)
    paras = text.split('\n\n')
    out = []
    for para in paras:

        # filter out new lines in the middle of paragraphs,
        # remove headers
        # and remove double whitespaces
        para = filter_newlines(para)
        para = header_footer_filter(para)
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
        #   combine letter -> accent strings from bad decoding to combined letter/accent
        #   e.g a´ gets converted to á
        para = ditch_combining_diacritics(fix_unicode.fix_unicode(remove_cid(remove_leading_and_trailing_nums(para))))
        if para != '':
            # only append if not empty
            out.append(para)

        # remove empty strings from prev step
        for i in out:
            if not i:
                out.remove(i)

    return '\n\n'.join(out)

text = """Journal of Clinical Laboratory Analysis 12:98–107 (1998)

Optimal Conditions of Immune Complex Transfer Enzyme Immunoassays for Antibody IgGs to HIV-1 Using Recombinant p17, p24, and Reverse Transcriptase as Antigens Seiichi Hashida,1 Setsuko Ishikawa,1 Kazuya Hashinaka,1 Ichiro Nishikata,1 Shinichi Oka,2 Kaoru Shimada,2 Atsushi Saito,3 Akihisa Takamizawa,4 Hideo Shinagawa,3 and Eiji Ishikawa1* 1Department of Biochemistry, Miyazaki Medical College, Kiyotake, Miyazaki, Japan 2Department of Infectious Diseases, Institute of Medical Science, University of Tokyo, Tokyo, Japan 3Department of Molecular Microbiology, Research Institute for Microbial Diseases, Osaka University, Osaka, Japan 4Kanonji Institute, The Research Foundation for Microbial Diseases of Osaka University, Kanonji, Kagawa, Japan

The immune complex transfer enzyme im- munoassays for antibody IgGs to p17, p24, and reverse transcriptase (RT) of HIV-1 were tested under various conditions. Antibody IgGs to HIV-1 were reacted for up to 20 hr with 2,4- dinitrophenyl-bovine serum albumin-re- combinant HIV-1 protein conjugates and recombinant HIV-1 protein-b -D-galactosidase conjugates, and the immune complexes formed, comprising the three components, were trapped onto polystyrene beads coated with (anti-2,4-dinitrophenyl group) IgG by in- cubation at 4–30°C for up to 2 hr with shaking and were transferred onto polystyrene beads coated with (antihuman IgG g -chain) IgG in the presence of excess of eN-2,4-dinitro- phenyl-L-lysine by incubation at 4–30°C for up to 2 hr with shaking. When serum randomly collected from an HIV-1 seropositive subject and serum included in an Western blot kit were tested, the formation of the immune complex was almost completed within 1 hr for antibody IgG to p17, within 1–2 hr for antibody IgG to p24 and within 4 hr for antibody IgG to RT. Even for antibody IgG to p17, however, the immune complex continued to be formed for at least 2 hr, when serum samples at early stages of HIV-1 infection were tested. Trap- ping and transferring of the immune com- plexes were faster at higher temperatures and were almost completed within 0.5–1.5 hr, although the amount of the immune complexes trapped and transferred at 25 and/or 30°C increased for 0.5–1 hr, but subsequently tended to decline. When the formation, trap- ping, and transferring of the immune com- plexes were performed for 0.5, 1, and 1 hr, respectively, with shaking followed by 1 hr assay of bound b -D-galactosidase activity, the sensitivities for antibody IgGs to p17, p24, and RT using 10 m l of serum samples were similar to or significantly higher than those of the corresponding previous immune complex transfer enzyme immunoassays using 10 m l of serum samples, in which the formation, trapping, and transferring of the immune com- plexes were performed for 3, 16, and 3 hr, respectively, without shaking, followed by 2.5 hr assay of bound b -D-galactosidase activ- ity, and the sensitivities for antibody IgGs to p17, p24, and RT using 100 m l of serum samples were 21–22-fold, 5.5–6.3-fold, and 5.3–6.0-fold, respectively, higher. When each period of time for the formation, trapping, and transferring of the immune complexes was prolonged to up to 4 hr, the sensitivities for antibody IgGs to p17, p24, and RT using 100 l of serum samples were improved 88–93- fold, 15–17-fold and 20–24-fold, respectively, as compared with those of the previous ones. J. Clin. Lab. Anal. 12:98–107, 1998. © 1998 Wiley-Liss, Inc.

Key words: antibody; human immunodeficiency virus type 1; p17; p24; reverse transcriptase

INTRODUCTION

Ultrasensitive enzyme immunoassays (immune complex transfer enzyme immunoassays) for antibody IgGs to p17, p24, and reverse transcriptase (RT) of HIV-1 have been developed using recombinant p17, p24, and RT (rp17, rp24, and rRT) as antigens (1–7). The immune complexes, comprising 2,4-

© 1998 Wiley-Liss, Inc.

*Correspondence to: Eiji Ishikawa, M.D., Department of Biochemistry, Miyazaki Medical College, Kiyotake, Miyazaki 889-16, Japan.

Received 13 August 1997; Accepted 20 August"""

print(pdf_filter(text, None))