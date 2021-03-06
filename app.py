from __future__ import unicode_literals
from flask import Flask, render_template, request, make_response
import xlrd
import pandas as pd
import html2text
import re
from Index import Index
from Highlight import Highlight
import pickle
import unicodedata as ud
import copy
from parsivar import FindStems
from parsivar import Normalizer
import datetime
import sys, os
from os import listdir
from collections import Counter
import numpy as np
import math

# from hazm import *

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


os.chdir(getScriptPath())

mode = "csv"
# mode="xlsx"
if mode == "csv":
    # filepaths = [f for f in listdir("./IR-project-data-phase-3-100k") if f.endswith('.csv')]
    # loc = pd.concat(map(pd.read_csv, filepaths))
    # print("df size",len(loc.index))
    loc = pd.read_csv("IR2.csv")
    # print(loc.head())
else:
    loc = pd.read_excel("IR.xlsx")
    # print(loc.head())
    # loc = 'IR.xlsx'
    # wb = xlrd.open_workbook(loc)
    # sheet = wb.sheet_by_index(0)
    # N=sheet.nrows

# N= len(loc.index)
N = 200
K = 10

text_maker = html2text.HTML2Text()
text_maker.ignore_links = True
text_maker.ignore_images = True
text_maker.strong_mark = " "

stop_words = ["در", "از", "این", "برای", "که", "و", "را", "با", "به", "است", "ها", "تا", "های", "کرد", "شد",
              "شده"]

d = datetime.datetime.today()
print('Current date and time: ', d)


def clean_html(raw_html):
    clean_r = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6}|<[^>]+>);')
    clean_text = re.sub(clean_r, '', raw_html)
    return clean_text


terms_dic = {}
empty_docs_dic = {}
docs_dic = {}


def clean_sentence(sentence):
    sentence = arToPersianChar(sentence)
    sentence = arToPersianNumb(sentence)
    sentence = yeksansaz(sentence)
    return sentence


def yeksansaz(userInput):
    dic = {
        # chandshekliha
        'آيينه': 'آينه',
        'اطاق': 'اتاق',
        'اتمبيل': 'اتومبيل',
        'اتوموبيل': 'اتومبيل',
        'بته': 'بوته',
        'بتّه': 'بوته',
        'توسي': 'طوسي',
        'بغچه': 'بقچه',
        'تزئين': 'تزيين',
        'چارپاره': 'چهارپاره',
        'دكّان': 'دكان',
        'سالون': 'سالن',
        'مليون': 'ميليون',
        'واگون': 'واگن',
        'هيجده': 'هجده',
        'هيژده': 'هجده',
        'هژده': 'هجده',
        'يخه': 'يقه',
        'ختمي': 'خطمي',
        'باطلاق': 'باتلاق',
        'غلطيدن': 'غلتيدن',
        'تآتر': 'تئاتر',
        'تاغ': 'تاق',
        ' آزوقه': 'آذوقه',
        'آزوغه': 'آذوقه',
        'قد قد': ' غد غد',
        'تومار': 'طومار',
        'كبّاده': 'كباده',
        'هيئت': 'هيأت',
        'زغال': 'ذغال',
        # kalamat ekhtesari
        'هـ . ش .': 'هجری شمسی',
        'هـ . ق .': 'هجری قمری',
        'ق . م .': 'قبل از میلاد',
        '(ص)': 'صلّی اللهُ علیه و آله و سَلَّم',
        '(س)': 'سلام الله علیه (علیها)',
        'ره': 'رحمه الله علیه',
        'رض': 'رَضِیَ الله عنهُ',
        'آبفا': 'آب و فاضلاب',
        'اتکا': 'اداره تدارکات کارمندان ارتش',
        'ج.ا.ا': 'جمهوری اسلامی ایران',
        'داعش': 'دولت اسلامی عراق و شام',
        'ساف': 'سازمان آزادی بخش فلسطین',
        'ساصد': 'سازمان صنایع دفاع',
        'ساواک': 'سازمان امنیت و اطلاعات کشور',
        'سمت': 'سازمان مطالعه و تدوین',
        'شابک': 'شماره استاندارد بین‌المللی کتاب',
        ' شبا': 'شماره حساب بانکی ایران',
        ' غ.ق.ق': 'غیرقابل قبول',
        'فتا': 'پلیس فضای تولید و تبادل اطلاعات ایران',
        'ناجا': 'نیروی انتظامی جمهوری اسلامی ایران',
        'پیامک': 'پیام کوتاه',
        'پ.ن': 'پی‌نوشت',
        'نهاجا': 'نیروی هوایی جمهوری اسلامی ایران',
        'نیما': 'نظام یکپارچهٔ معاملات ارزی',
        'گیگ': 'گیگابایت',
        'هما': 'هواپیمائی ملی ایران',
        'ن.م': 'نیروهای مسلح',
        'محک': 'مؤسسات خیریه حمایت از کودکان مبتلا به سرطان',
        'سمپاد': 'سازمان ملی پرورش استعدادهای درخشان',
        'آجا': 'ارتش جمهوری اسلامی ایران',
        'سیبا': 'سیستم یکپارچه بانک ملی ایران',
        'مگ': 'مگابایت',
        'kg': 'کیلوگرم',
        'g': 'گرم',
        'cm': 'سانتی متر',
        'm': 'متر',
        'km': 'کیلومتر',

    }
    return multiple_replace(dic, userInput)


def arToPersianNumb(number):
    dic = {
        '٠': '۰',
        '١': '۱',
        '٢': '۲',
        '٣': '۳',
        '٤': '۴',
        '٥': '۵',
        '٦': '۶',
        '٧': '۷',
        '٨': '۸',
        '٩': '۹',
        '0': '۰',
        '1': '۱',
        '2': '۲',
        '3': '۳',
        '4': '۴',
        '5': '۵',
        '6': '۶',
        '7': '۷',
        '8': '۸',
        '9': '۹',

    }
    return multiple_replace(dic, number)


def arToPersianChar(userInput):
    dic = {
        'ك': 'ک',
        'دِ': 'د',
        'بِ': 'ب',
        'زِ': 'ز',
        'ذِ': 'ذ',
        'شِ': 'ش',
        'سِ': 'س',
        'ى': 'ی',
        'ي': 'ی',
        'ئ': 'ی',
        'آ': 'ا',
        'اٍ': 'ا',
        'اٌ': 'ا',
        'اً': 'ا',
        'اَ': 'ا',
        'ۀ': 'ه',
        'أ': 'ا',
        'ؤ': 'و',
        'ء': 'ی',
        # eerab
        '\u064B': '',  # FATHATAN
        '\u064C': '',  # DAMMATAN
        '\u064D': '',  # KASRATAN
        '\u064E': '',  # FATHA
        '\u064F': '',  # DAMMA
        '\u0650': '',  # KASRA
        '\u0651': '',  # SHADDA
        '\u0652': '',  # SUKUN
        # halp space
        # '\u200c': '',  #half space
        '\u1680': '\u200c',  # OGHAM SPACE
        '\u180E': '\u200c',  # MONGOLIAN VOWEL SEPARATOR
        '\u2006': '\u200c',  # SIX-PER-EM SPACE
        '\u2008': '\u200c',  # PUNCTUATION SPACE
        '\u2009': '\u200c',  # THIN SPACE
        '\u200A': '\u200c',  # HAIR SPACE
        '\u200B': '\u200c',  # ZERO WIDTH SPACE
        '\u202F': '\u200c',  # NARROW NO-BREAK SPACE
        '\u205F': '\u200c',  # MEDIUM MATHEMATICAL SPACE
        '\uFEFF': '\u200c',  # ZERO WIDTH NO-BREAK SPACE
        # spaces
        '\u00A0': '\u0020',  # nobreak space
        '\u2000': '\u0020',  # EN QUAD
        '\u2001': '\u0020',  # EM QUAD
        '\u2002': '\u0020',  # EN SPACE (nut)
        '\u2003': '\u0020',  # EM SPACE (mutton)
        '\u2004': '\u0020',  # THREE-PER-EM SPACE (thick space)
        '\u2005': '\u0020',  # FOUR-PER-EM SPACE (mid space)
        '\u2007': '\u0020',  # FIGURE SPACE
        '\u3000': '\u0020',  # IDEOGRAPHIC SPACE

        # emoji
        '\uF600': '',  # grinning face
        '\uF603': '',  # grinning face with big eyes
        '\uF604': '',  # grinning face with smiling eyes
        '\uF601': '',  # beaming face with smiling eyes
        '\uF605': '',  # grinning face with sweat
        '\uF923': '',  # rolling on the floor laughing
        '\uF602': '',  # face with tears of joy
        '\uF642': '',  # slightly smiling face
        '\uF643': '',  # upside-down face
        '\uF609': '',  # winking face
        '\uF60A': '',  # smiling face with smiling eyes
        '\uF607': '',  # smiling face with halo
        '\uF970': '',  # smiling face with 3 hearts
        '\uF60D': '',  # smiling face with heart-eyes
        '\uF929': '',  # star-struck
        '\uF618': '',  # face blowing a kiss
        '\uF617': '',  # kissing face
        '\uF61A': '',  # kissing face with closed eyes
        '\uF619': '',  # kissing face with smiling eyes
        '\uF60B': '',  # face savoring food
        '\uF61B': '',  # face with tongue
        '\uF61C': '',  # winking face with tongue
        '\uF92A': '',  # zany face
        '\uF61D': '',  # squinting face with tongue
        '\uF911': '',  # money-mouth face
        '\uF917': '',  # hugging face
        '\uF92D': '',  # with hand over mouth
        '\uF92B': '',  # shushing face
        '\uF914': '',  # thinking face
        '\uF910': '',  # zipper-mouth face
        '\uF928': '',  # face with raised eyebrow
        '\uF610': '',  # neutral face
        '\uF611': '',  # expressionless face
        '\uF636': '',  # face without mouth
        '\uF60F': '',  # smirking face
        '\uF612': '',  # unamused face
        '\uF644': '',  # face with rolling eyes
        '\uF62C': '',  # grimacing face
        '\uF925': '',  # lying face
        '\uF60C': '',  # relieved face
        '\uF614': '',  # pensive face
        '\uF62A': '',  # sleepy face
        '\uF924': '',  # drooling face
        '\uF634': '',  # sleeping face
        '\uF637': '',  # face with medical mask
        '\uF912': '',  # face with thermometer
        '\uF915': '',  # face with head-bandage
        '\uF922': '',  # nauseated face

    }
    return multiple_replace(dic, userInput)


def multiple_replace(dic, text):
    pattern = "|".join(map(re.escape, dic.keys()))
    return re.sub(pattern, lambda m: dic[m.group()], str(text))


def clean_all(document):
    clean = ''
    for sentence in document:
        sentence = clean_sentence(sentence)
        clean += sentence
    return clean


def steaming(splited):
    pat = [
        'یی',
        'ی',
        'ها',
        'تر',
        'ترین',
        'ان',
        'ات',
        'ام',
        'ایم',
        'ید',
        'ند',
        'یم',
        'ید',
        'یم',
        'گر',
        'گری'

    ]

    return st(pat, splited)


def st(pat, splited):
    steammed = ''

    for word in splited:
        for suffix in pat:
            if word.endswith(suffix):
                token = word[0: (len(word) - len(suffix))]
                steammed += token + ' '
    return steammed


def doc_freq(word, DF):
    c = 0
    try:
        c = DF[word]
    except:
        pass
    return c


try:

    pickle_in1 = open("dict.pickle", "rb")
    print("loading inverted index")
    terms_dic = pickle.load(pickle_in1)
    pickle_in1.close()

    pickle_in2 = open("doc.pickle", "rb")
    docs_dic = pickle.load(pickle_in2)
    pickle_in2.close()

    print("loading tf_idf matrix")
    pickle_in3 = open("tfidf.pickle", "rb")
    Dtf_idf = pickle.load(pickle_in3)
    pickle_in3.close()

    pickle_in4 = open("df.pickle", "rb")
    DFf = pickle.load(pickle_in4)
    pickle_in4.close()

except (OSError, IOError) as e:

    for j in range(1, N):
        empty_docs_dic[j] = []
        news = loc.at[j, 'content']
        # news = sheet.cell_value(j, 5)

        news = text_maker.handle(news)
        clean_html(news)
        # remove persian punctuations
        news = ''.join(c for c in news if not ud.category(c).startswith('P'))

        normolized_news = clean_all(news)

        my_normalizer = Normalizer()
        parsivar_normalized = my_normalizer.normalize(normolized_news)

        splitednews = parsivar_normalized.split()

        docs_dic[j] = splitednews.copy()

        my_stemmer = FindStems()
        for i in range(len(splitednews)):
            splitednews[i] = my_stemmer.convert_to_stem(splitednews[i]).split('&')[0]
        # print(splitednews)

        # print(normolized_news)

        # splited = splitednews.copy()

        # steammed = steaming(splited)
        # steammed_splitted = steammed.split()
        # print(steammed)

        # adding terms to dictionary
        i = 0
        for term in splitednews:
            # if term not in stop_words:
            if term not in terms_dic:
                terms_dic[term] = Index()
            terms_dic[term].add(j, i)
            i += 1

    DFf = {}
    total_vocab_size = len(terms_dic)
    for term in terms_dic:
        DFf[term] = len(terms_dic[term].index_dic)

    doc = 0

    tf_idf = {}
    print("counter is running ")
    for i in range(1, N):

        tokens = docs_dic[i]

        counter = Counter(tokens)
        # print(counter)
        words_count = len(tokens)
        # print(words_count)

        # print("this the document number")
        # print(i)
        if words_count != 0:
            for token in terms_dic:
                tf = counter[token] / words_count
                df = doc_freq(token, DFf)
                # we can now use different formula for document term weight
                idf = np.log10((N + 1) / (df + 1))
                tf_idf[doc, token] = tf * idf
        doc += 1

    Dtf_idf = np.zeros((N, total_vocab_size))
    for i in tf_idf:
        try:
            ind = list(terms_dic.keys()).index(i[1])
            Dtf_idf[i[0]][ind] = tf_idf[i]
        except:
            pass

    pickle_out1 = open("dict.pickle", "wb")
    print("making the inverted index")
    pickle.dump(terms_dic, pickle_out1)
    pickle_out1.close()

    pickle_out2 = open("doc.pickle", "wb")
    pickle.dump(docs_dic, pickle_out2)
    pickle_out2.close()

    pickle_out3 = open("tfidf.pickle", "wb")
    pickle.dump(Dtf_idf, pickle_out3)
    pickle_out3.close()

    pickle_out4 = open("df.pickle", "wb")
    pickle.dump(DFf, pickle_out4)
    pickle_out4.close()

    d2 = datetime.datetime.today()
    print('Current date and time: ', d2)
    print("difference", d2 - d)


# freq_list = []
# for term in terms_dic:
#     freq = terms_dic[term].frequency
#     freq_list.append(freq)
#     if 200<freq < 300:
#         print(term, end=" : ")
#         print(freq)
#
# freq_list.sort(reverse=True)
# print(freq_list)


# for t in example_dict:
#     print(t + ": ")
#     print("frequency: ", end="")
#     print(example_dict[t].frequency)
#     for i in example_dict[t].index_dic:
#         print(i, end="")
#         print(": ", end="")
#         print((example_dict[t].index_dic[i]))


# printing resulted dictionary

# for t in terms_dic:
#     print(t + ": ")
#     print("frequency: ", end="")
#     print(terms_dic[t].frequency)
#     for i in terms_dic[t].index_dic:
#         print(i, end="")
#         print(": ", end="")
#         print((terms_dic[t].index_dic[i]))

def cosine_sim(a, b):
    aa = np.linalg.norm(a)
    bb = np.linalg.norm(b)
    cos_sim = 0
    if aa != 0 and bb != 0:
        cos_sim = np.dot(a, b) / (aa * bb)
    return cos_sim


def gen_vector(tokens):
    Q = np.zeros((len(terms_dic)))

    counter = Counter(tokens)
    print("counter", counter)
    words_count = len(tokens)

    query_weights = {}

    for token in np.unique(tokens):

        tf = counter[token] / words_count
        df = doc_freq(token, DFf)
        idf = math.log10((N + 1) / (df + 1))

        try:
            ind = list(terms_dic.keys()).index(token)
            Q[ind] = tf * idf
        except:
            pass
    return Q


def cosine_similarity(k, query):
    print("Cosine Similarity")
    # tokens = (str(query))
    tokens = query
    print("\nQuery:", query)
    print("")
    print(tokens)

    d_cosines = []

    query_vector = gen_vector(tokens)
    i = 0
    zeros = []
    for d in Dtf_idf:
        cosine_s = cosine_sim(query_vector, d)
        if cosine_s == 0:
            zeros.append(i)
        d_cosines.append(cosine_s)
        i += 1
    print("zeros ", zeros)
    print("cosine ", d_cosines)
    out = np.array(d_cosines).argsort()[-k:][::-1]
    out = [x + 1 for x in out if x not in zeros]

    print("out ", out)
    return out


def page_result(add, highlights, page=1, number=10):
    data = []
    # wb = xlrd.open_workbook(add)
    # sheet = wb.sheet_by_index(0)
    i = 1
    for key in highlights:
        if i in range(((page - 1) * number) + 1, page * number + 1):
            # data.append(sheet.row_values(key) + [key])
            a = loc.iloc[[key]].to_numpy()[0]
            data.append(np.append(a, [key]))
        i += 1
    print("dataf")
    print(data[0][0])
    return data


def find_express(query):
    expression = re.findall(r'"([^"]*)"', query)
    print("hi")
    print(expression)
    return expression


def no_express(query, expression):
    for i in expression:
        query = query.replace(i, "")
        query = query.replace('"', "")

    query_words = query.split()
    print("query_words")
    print(query_words)
    return query_words


def not_terms(without_express):
    not_terms = []
    normal_words = without_express.copy()
    for i in normal_words:
        if i == '!':
            not_terms.append(normal_words[normal_words.index(i) + 1])
            normal_words.remove(normal_words[normal_words.index(i) + 1])
            normal_words.remove(i)

    return normal_words, not_terms


def query_processing(query):
    expression = find_express(query)
    without_express = no_express(query, expression)
    normal_words, not_vocabs = not_terms(without_express)
    print("expression : %s" % expression)
    print("without expression : %s" % without_express)
    print("notVocab is %s" % not_vocabs)
    print("normalwords is %s" % normal_words)
    return expression, normal_words, not_vocabs


def intersect(terms, prev_result):
    result_index = {}
    if terms:
        print("terms[0]")
        print(terms[0])
        if terms[0] in prev_result:
            # :)))))))))))
            result_index = copy.deepcopy(prev_result[terms[0]].index_dic)
            terms.pop(0)
            print("terms after pop")
            print(terms)
            while result_index is not None and terms:
                if terms[0] in prev_result:
                    result_did = result_index.keys() & prev_result[terms[0]].index_dic.keys()
                    print("result_did")
                    print(result_did)

                    # remove doc ids which don't contain all of the words in expression
                    temp = result_index.copy()
                    for did in temp.keys():
                        if did not in result_did:
                            result_index.pop(did)

                        else:
                            result_index[did] += prev_result[terms[0]].index_dic[did]

                    print("terms")
                    print(terms)
                    terms.pop(0)
    for id in result_index:
        result_index[id].sort()
    return result_index


def expression_intersect(expressions):
    current_index = {}
    expressions_term_index = {}
    while expressions:
        split_ex = expressions[0].split()
        count = len(split_ex)
        if all(t in terms_dic for t in split_ex):
            print("expressions_term_index 0")
            print(terms_dic[split_ex[0]].index_dic)
            current_index = terms_dic[split_ex[0]].index_dic
            split_ex.pop(0)
            while current_index is not None and split_ex:
                term_index_dic = terms_dic[split_ex[0]].index_dic
                print("term_index_dic")
                print(term_index_dic)
                tmp = {}
                for did in current_index:
                    if did in term_index_dic.keys():
                        for pos in current_index[did]:
                            next_pos = pos + 1

                            if next_pos in term_index_dic[did]:
                                # add this term to tmp
                                if did in tmp.keys():
                                    tmp[did].append(next_pos)
                                else:
                                    tmp[did] = [next_pos]

                current_index = tmp
                print("tmp")
                print(tmp)
                split_ex.pop(0)
        for doc in current_index:
            for pos in current_index[doc]:
                for t in range(-count + 1, 1):
                    if doc in expressions_term_index.keys():
                        expressions_term_index[doc].append(pos + t)
                    else:
                        expressions_term_index[doc] = [pos + t]
        expressions.pop(0)
    return expressions_term_index


def res(whole, resultVocab):
    diffKeys = set(whole.keys()) - set(resultVocab)
    w = dict()
    for key in diffKeys:
        w[key] = whole.get(key)

    return w


def docs_to_dic(docs, prev_dic):
    result_dic = {}
    for doc_id in docs:
        for term in prev_dic:
            tmp = prev_dic[term]
            if doc_id in tmp.index_dic.keys():
                result_dic[term] = tmp
    return result_dic


def find_highlights(result):
    # a dic which map doc ids to highlight text of the doc
    highlights = {}
    for id in result:
        c = 0
        text = docs_dic[id]
        # print(text)
        length = len(text)
        for pos in result[id]:
            if c == 0 or not (pos1 - 5 < pos < pos1 + 6):
                for i in range(pos - 5, pos):
                    if -1 < i:
                        # print(i)
                        if id in highlights.keys():
                            highlights[id].append(Highlight(text[i], False))
                        else:
                            highlights[id] = [Highlight(text[i], False)]
                if id in highlights.keys():
                    highlights[id].append(Highlight(text[pos], True))
                else:
                    highlights[id] = [Highlight(text[pos], True)]
                # highlights.append(Highlight(text[pos], True))
                for i in range(pos + 1, pos + 6):
                    if i < length:
                        # print(i)
                        highlights[id].append(Highlight(text[i], False))
                highlights[id].append(Highlight(" ... ", False))
                pos1 = pos
            else:
                for h in highlights[id]:
                    if h.word == text[pos]:
                        h.highlight()
            c = 1
    return highlights


def query_result(expressions, normal_words, not_vocabs):
    norm = normal_words.copy()
    exp = expressions.copy()
    nots = not_vocabs.copy()

    # normal words
    print("norm")
    print(norm)

    # first find docs which contain expressions
    if exp:
        e_result_docs = expression_intersect(exp)
        print("e_result")
        print(e_result_docs)

        e_result_dic = docs_to_dic(e_result_docs, terms_dic)
    else:
        e_result_docs = empty_docs_dic
        e_result_dic = terms_dic

    # then find docs which contain normal words
    if norm:
        norm_result_docs = intersect(norm, e_result_dic)
        print("normal result", norm_result_docs)

        norm_result_dic = docs_to_dic(norm_result_docs, e_result_dic)
    else:
        norm_result_docs = e_result_docs
        norm_result_dic = e_result_dic

    # not_vocabularies
    if nots:
        result_vocab = {}
        for i in nots:
            print("not word")
            print(i)
            if i in norm_result_dic:
                vocab_id = norm_result_dic[i].index_dic.keys()
                print("vocabID")
                print(vocab_id)
                result_vocab = result_vocab | vocab_id
        print("result of the vocab %s" % result_vocab)
        whole_result = res(norm_result_docs, result_vocab)
    else:
        whole_result = norm_result_docs
    print("this is result")
    print(whole_result)

    highlights = find_highlights(whole_result)

    return whole_result, highlights


highlights = {}
total_page_num = 0
last_page_len = 0


@app.route('/')
def hello_world():
    return render_template('main.html')


@app.route('/search/<int:page_num>', methods=['POST', 'GET'])
def search(page_num):
    global highlights, total_page_num, last_page_len, query, total_res
    if page_num is None:
        page_num = 1
    if request.method == 'POST':
        query = request.form['query']
        sort = request.form['sort_options']
        print('sort : %s' % sort)

        # query = ''.join(c for c in query if not ud.category(c).startswith('P'))

        normalized_query = clean_all(query)

        my_normalizer = Normalizer()
        parsivar_normalized = my_normalizer.normalize(normalized_query)

        # query_splitted = normolized_query.split()
        # rtp_query = ""
        # for q in query_splitted:
        #     if q not in stop_words:
        #         rtp_query += q
        #         rtp_query += " "
        # print(rtp_query)

        print(parsivar_normalized)
        splited_query = parsivar_normalized.split()
        my_stemmer = FindStems()
        stemer_result = ""
        for i in range(len(splited_query)):
            stemer_result += my_stemmer.convert_to_stem(splited_query[i]).split('&')[0] + " "
        print("stemer result: ", stemer_result)

        expression, normalWords, notVocabs = query_processing(stemer_result)
        result, highlights = query_result(expression, normalWords, notVocabs)
        print(sort)
        if sort == "connection":
            connectionresult = cosine_similarity(K, stemer_result.split())
            print("cos res ")
            print(connectionresult)

            print("actual res ")
            print(result)

            similarresult = []

            # TODO inja bayad result to bar hasb connection moratab beshe yeki dige ham inke in natije jadide neshon dade beshe
            for did in connectionresult:
                for didr in result:
                    if did == didr:
                        similarresult.append(did)
            print("similarresult")
            print(similarresult)
            index_res_rest = [x for x in result if x not in similarresult]
            con_res_rest = [x for x in connectionresult if x not in similarresult]
            sorted_index_res = similarresult + index_res_rest
            # result_similarity = OrderedDict(sorted(highlights.items(), key=lambda pair: for_highlight_sort.index(pair[0])))
            print("changed  res ")
            print(sorted_index_res)

            total_res = sorted_index_res + con_res_rest
            print("rs ", total_res)
        else:
            total_res = result

        length = len(total_res)
        total_page_num = int(length / 10) + 1
        last_page_len = length % 10

    page_len = 10
    if page_num == total_page_num:
        page_len = last_page_len

    resp = make_response(
        render_template('search.html', prequery=query, page=page_num,
                        listing=page_result(loc, total_res, page_num, 10),
                        total_pages=total_page_num, highlights=highlights,
                        len=page_len))

    return resp


@app.route('/result/<int:news>', methods=['POST', 'GET'])
def shownews(news):
    resp = make_response(
        render_template('result.html', listing=loc.iloc[[news]].to_numpy()[0])
    )
    return resp


if __name__ == '__main__':
    app.run(debug=True)
