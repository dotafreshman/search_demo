from flask import Flask, request, render_template
import time
from rank_bm25 import BM25Plus
import pandas as pd
from snownlp import SnowNLP
# from cocoNLP.config.phrase import rake
# import cocoNLP
import pandas as pd
from collections import Counter
import jionlp as jio
import pickle
import time
import re

app = Flask(__name__)


# textname = "text.csv"
textname = "观点抽取.xlsx"
queries = ""
tofile = "result"
stop = ""
corpus = ""
dict = {}

class prores:
    resstr = "";
    resl = [];


# process函数，从cocoNLP的处理结果中，提取分词token与高频词部分，以class prores形式返回
def process(key_phrase):
    res = prores();
    for t in key_phrase:
        res.resstr += t + " "

    res.resl = Counter(key_phrase).most_common(20)
    return res;

# def remStp(words):
#     ans = ""
#     for word in words:
#         if word not in stop: ans += word
#     return ans

def addQ(query, lis):
    for i in range(len(lis)):
        lis[i] = re.sub(query,' <span> '+query+' </span> ', lis[i])
    return lis


# 根据搜索词生成表格，关键函数
def fetch(query):
    col1_ori = []
    col2_tok = []
    col_label = []
    col3_freq = []
    col0_q = []

    # r = rake.Rake()
    t0 = time.perf_counter()
    # tokenized_corpus = [remStp(SnowNLP(doc).words) for doc in corpus]
    tokenized_corpus = corpus
    print(str(time.perf_counter() - t0)+" remStp time")
    # print(tokenized_corpus)

    # 基于bm25算法，按照搜索词从评论文档检索
    #

    # tokenized_query = SnowNLP(query).words
    tokenized_query = query
    # try:
    #     f = open("bm25.pkl", 'rb')
    #     # pickle.dump(bm25, f)
    #     bm25 = pickle.load(f)
    #     f.close()
    # except:
    # f = open("bm25.pkl", 'wb')
    bm25 = BM25Plus(tokenized_corpus)
    # pickle.dump(bm25, f)

    # f.close()

    res = bm25.get_top_n(tokenized_query, tokenized_corpus,n=20)
    # 遍历检索结果，对每条sen单独处理
    for sen in res:
        # 使用cocoNLP算法从sen中观点挖掘
        # r.extract_keywords_from_sentences([sen], 2, 4)
        #
        # ranked_words = r.get_ranked_phrases()
        #
        # ranked_words_score = r.get_ranked_phrases_with_scores()
        key_phrase = jio.keyphrase.extract_keyphrase(sen)

        # 处理挖掘信息，获得表格对应的4个字段：检索词，评论，分词，高频词
        t0 = time.perf_counter()
        theprocess = process(key_phrase)
        print(str(time.perf_counter() - t0)+" process time")
        col0_q += [query]
        col1_ori += [sen]
        col_label += [dict[sen]]
        col2_tok += [theprocess.resstr]
        col3_freq += [theprocess.resl]
        # print(sen+"\t"+str(ranked_words_score))
    df = pd.DataFrame({"query": col0_q, "text": col1_ori, "label":col_label, "token": col2_tok, "frequency": col3_freq})
    return df


# def thesystem(queries, textname, tofile):
#     text = pd.read_excel(textname, names=["text"], encoding='utf-8')
#     # print(text["text"])
#     global corpus, stop
#     corpus = text["text"].tolist()
#     stop = [line.strip() for line in open('stop_words.txt', encoding='utf-8').readlines()]
#
#     df = fetch(queries[0]);
#     for i in range(1, len(queries)):
#         df = df.append([fetch(queries[i])], ignore_index=True)
#     df.to_csv(tofile)
def thesystem(query):
    text = pd.read_excel(textname, names=["text","pred label"], encoding='utf-8')
    for i in range(len(text)):
        dict[text.iloc[i]["text"]] = text.iloc[i]["pred label"]
    # print(text["text"])
    global corpus, stop
    corpus = text["text"].tolist()
    stop = [line.strip() for line in open('stop_words.txt', encoding='utf-8').readlines()]
    t0 = time.perf_counter()
    df = fetch(query);
    print(str(time.perf_counter() - t0)+"fetch time")
    # for i in range(1, len(queries)):
    #     df = df.append([fetch(queries[i])], ignore_index=True)
    df.to_csv(tofile+str(time.time())+".csv")
    the = df[["text","label"]]
    print(the)
    return the


@app.route('/')
def hello_world():
    return "hello, world!"

@app.route('/system',methods=['GET','POST'])
def system():
    if request.method=='POST':
        # queries = []
        # for i in range(1, 11):
        #     queries += [request.form['query '+str(i)]]
        # textname = request.form['inputFileName']
        # tofile = request.form['outputFileName']
        query = request.form['query']

        textlist = thesystem(query)
        # textlist = [query]+['\n']+addQ(query,list(textlist))

        a = textlist["text"]; a = [query]+addQ(query, list(a))
        b = textlist["label"];b = ["观点抽取标签"]+addQ(query, list(b))
        c = []
        for i in range(len(a)):
            c+=[[a[i],b[i]]]

        return render_template('index.html', name=1, movies=c)
    return render_template('index.html', names=0)


if __name__ == '__main__':
    print('starting Flask app', app.name)
    app.run(debug=True)