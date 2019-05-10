# coding=utf-8
from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS


def read_statement():
    # 读取新闻的数据
    csv = pd.read_csv('liar_dataset/liar_dataset/statement.csv', sep=',', header=None, index_col=False,
                      names=['label', 'statement', 'speaker', 'year', 'month', 'url'])
    return csv


def read_speakerinfo():
    # 读取人物的数据
    csv = pd.read_csv('liar_dataset/liar_dataset/speaker.csv', sep=',', header=None, index_col=False,
                      names=['speaker', 'party', 'stateInfo'])
    return csv


def count_word(s):
    punc = ['"', '(', ')', ',', '.', '$', ':', '?', '!', '%', '‘']
    cnt = {}
    # i为每个statement
    for i in s:
        # 删除statement中的标点符号
        i = i.replace('’', "'")
        for p in punc:
            i = i.replace(p, '')
        # _i为每个单词
        for _i in i.lower().split(' '):
            _i = _i.strip()
            if not _i.isdigit():
                cnt[_i] = cnt.get(_i, 0) + 1
    d = [{"name": k, "value": v} for k, v in cnt.items() if k not in stop_words]
    return d


def count_ch(fd):
    items = ['True', 'Mostly True', 'Half-True', 'Mostly False', 'False', 'Pants on Fire!']
    credit = []
    for item in items:
        credit.append(fd.count(item))
    ch = {"TrueCounts": credit[0], "mostlyTrueCounts": credit[1], "halfTrueCounts": credit[2],
          "mostlyFalseCounts": credit[3], "FalseCounts": credit[4], "onFireCounts": credit[5]}
    return ch

def count_ch_binary(fd):
    items = ['True', 'Mostly True', 'Half-True', 'Mostly False', 'False', 'Pants on Fire!']
    credit = []
    for item in items:
        credit.append(fd.count(item))
    ch = {"True": credit[0] + credit[1], "False": credit[2] + credit[3] + credit[4] + credit[5]}
    return ch


# 程序开始时，读取数据
app = Flask(__name__)
CORS(app, supports_credentials=True)
data = read_statement()
data_s = read_speakerinfo()

# 去掉数据中的回车符和空格
data['speaker'] = data['speaker'].apply(lambda x:x.replace("\n",""))
data_s['speaker'] = data_s['speaker'].apply(lambda x:x.lstrip())
data['statement'] = data['statement'].apply(lambda x:x.rstrip())

# 读取停止词表
with open('liar_dataset/liar_dataset/stopword.txt', 'r') as f:
    stop_words = f.read().splitlines()
    f.close()


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/speaker/states')
def speaker_statement():
    # 接受参数sname，返回该speaker所有statement
    sname = request.args.get('sname')
    d = []
    if sname is None:
        # 没有传入sname,返回状态值2
        status = 2
    else:
        s = data[data['speaker'] == sname]
        if s.shape[0] == 0:
            # 没有speaker的数据，返回状态值1
            status = 1
        else:
            # 正常，返回状态值0
            d = s['statement'].values.tolist()
            status = 0
    r = {'code': status, 'data': d}
    return jsonify(r)


@app.route('/speaker/info')
def speaker_info():
    s_name = request.args.get('sname')
    d = []
    if s_name is None:
        status = 2
    else:
        fd = data_s[data_s['speaker'] == s_name]
        if fd.shape[0] == 0:
            status = 1
        else:
            status = 0
            party = fd['party'].values.tolist().pop()
            state = fd['stateInfo'].values.tolist().pop()
            d = {"party": party, "stateInfo": state}
    r = {'code': status, 'data': d}
    return jsonify(r)


@app.route('/wordcnt/speaker')
def word_cnt_by_speaker():
    # 接受参数sname,year
    # 若year为空，返回speaker的所有statements中词的统计
    # 若year不空，返回speaker这一年的statements中词的统计
    sname = request.args.get('sname')
    year = request.args.get('year')
    d = []
    if sname is None:
        # 没有传入sname,返回状态值2
        status = 2
    elif year is not None and not year.isdigit():
        status = 2
    else:
        # 判断year是否为空
        if year is None or int(year) == 0:
            fd = data[data['speaker'] == sname]
        else:
            fd = data[(data['speaker'] == sname) & (data['year'] == int(year))]
        # 判断数据是否为空
        if fd.shape[0] == 0:
            # 没有找到数据，返回状态值1
            status = 1
        else:
            # 正常，返回状态值0
            status = 0
            s = fd['statement'].values
            d = count_word(s)
    r = {'code': status, 'data': d}
    return jsonify(r)


@app.route('/wordcnt/time')
def word_cnt_by_year():
    # 接受参数year,month
    # 若month为空，返回年份year所有statements中词的统计
    # 若month不空，返回年份year月份month所有statements中词的统计
    year = request.args.get('year')
    month = request.args.get('month')
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December', '0']
    d = []
    if year is None:
        # 没有传入year,返回状态值2
        status = 2
    elif not year.isdigit():
        status = 2
    elif month not in months:
        status = 2
    else:
        # 判断month是否为空
        if month is None or (month.isdigit() and int(month) == 0):
            fd = data[data['year'] == int(year)]
        else:
            fd = data[(data['year'] == int(year)) & (data['month'] == month)]
        # 判断数据是否为空
        if fd.shape[0] == 0:
            # 没有找到数据，返回状态值1
            status = 1
        else:
            # 正常，返回状态值0
            status = 0
            s = fd['statement'].values
            d = count_word(s)
    r = {'code': status, 'data': d}
    return jsonify(r)


@app.route('/wordcnt/party')
def word_cnt_by_party():
    party = request.args.get('party')
    year = request.args.get('year')
    d = []
    if party is None:
        status = 2
    elif year is not None and not year.isdigit():
        status = 2
    else:
        st = []
        speaker = data_s[data_s['party'] == party]['speaker'].values.tolist()
        for sname in speaker:
            if year is None or int(year) == 0:
                fd = data[data['speaker'] == sname]['statement'].values.tolist()
                st.extend(fd)
            else:
                fd = data[(data['speaker'] == sname) & (data['year'] == int(year))]['statement'].values.tolist()
                st.extend(fd)
        if len(st) == 0:
            status = 1
        else:
            status = 0
            d = count_word(st)
    r = {'code': status, 'data': d}
    return jsonify(r)


@app.route('/ch/year')
def credit_history_by_year():
    year1 = request.args.get('year1')
    year2 = request.args.get('year2')
    d = []
    if year1 is None:
        status = 2
    elif not year1.isdigit():
        status = 2
    elif year2 is None:
        fd = data[data['year'] == int(year1)]
        if fd.shape[0] == 0:
            status = 1
        else:
            status = 0
            ch = fd['label'].values.tolist()
            d = {year1: count_ch(ch)}
    elif not year2.isdigit():
        status = 2
    elif year1 > year2:
        status = 2
    else:
        status = 0
        for year in range(int(year1), int(year2)+1):
            fd = data[data['year'] == year]
            if fd.shape[0] != 0:
                ch = fd['label'].values.tolist()
                c = {year:count_ch(ch)}
                d.append(c)
        if len(d) == 0:
            status = 1
    r = {'code': status, 'data': d}
    return jsonify(r)


@app.route('/ch/speaker')
def credit_history_by_speaker():
    sname = request.args.get('sname')
    year1 = request.args.get('year1')
    year2 = request.args.get('year2')
    d = []
    if sname is None:
        status = 2
    elif year1 is not None and not year1.isdigit():
        status = 2
    elif year2 is not None and not year2.isdigit():
        status = 2
    elif year1 is not None and year2 is not None and year1 > year2:
        status = 2
    elif year2 is None or (year2.isdigit() and int(year2) == 0):
        if year1 is None or (year1.isdigit and int(year1) == 0):
            fd = data[data['speaker'] == sname]
        else:
            fd = data[(data['speaker'] == sname) & (data['year'] == int(year1))]
        if fd.shape[0] == 0:
            status = 1
        else:
            status = 0
            ch = fd['label'].values.tolist()
            d = count_ch(ch)
    else:
        status = 0
        for year in range(int(year1), int(year2) + 1):
            fd = data[(data['speaker'] == sname) & (data['year'] == int(year))]
            if fd.shape[0] != 0:
                ch = fd['label'].values.tolist()
                c = {year: count_ch(ch)}
                d.append(c)
        if len(d) == 0:
            status = 1
    r = {'code': status, 'data': d}
    return jsonify(r)


@app.route('/ch/party')
def credit_history_by_party():
    party = request.args.get('party')
    year1 = request.args.get('year1')
    year2 = request.args.get('year2')
    d = []
    if party is None:
        status = 2
    elif year1 is not None and not year1.isdigit():
        status = 2
    elif year2 is not None and not year2.isdigit():
        status = 2
    elif year1 is not None and year2 is not None and year1 > year2:
        status = 2
    else:
        speaker = data_s[data_s['party'] == party]['speaker'].values.tolist()
        labels = []
        if year2 is None or (year2.isdigit() and int(year2) == 0):
            for sname in speaker:
                if year1 is None or (year1.isdigit() and int(year1) == 0):
                    fd = data[data['speaker'] == sname]['label'].values.tolist()
                    labels.extend(fd)
                else:
                    fd = data[(data['speaker'] == sname) & (data['year'] == int(year1))]['label'].values.tolist()
                    labels.extend(fd)
            if len(labels) == 0:
                status = 1
            else:
                status = 0
                d = count_ch(labels)
        else:
            status = 0
            for year in range(int(year1), int(year2) + 1):
                for sname in speaker:
                    fd = data[(data['speaker'] == sname) & (data['year'] == int(year))]
                    if fd.shape[0] != 0:
                        ch = fd['label'].values.tolist()
                        labels.extend(ch)
                if len(labels) != 0:
                    c = {year: count_ch(labels)}
                    d.append(c)
            if len(d) == 0:
                status = 1
    r = {'code': status, 'data': d}
    return jsonify(r)


@app.route('/ch/time')
def credit_history_by_time():
    from collections import defaultdict
    binary = request.args.get('binary')
    months = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7,
              'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}
    t = []
    counts = ["TrueCounts", "mostlyTrueCounts", "halfTrueCounts",
              "mostlyFalseCounts", "FalseCounts", "onFireCounts"]
    c = defaultdict(list)
    years = data['year'].values.tolist()
    years = list(set(years))
    for year in range(min(years), max(years) + 1):
        for month in months.keys():
            fd = data[(data['year'] == year) & (data['month'] == month)]
            if fd.shape[0] != 0:
                t.append(str(year) + '/' + str(months[month]))
                ch = fd['label'].values.tolist()
                if binary == 'true':
                    ch = count_ch_binary(ch)
                    c['True'].append(ch['True'])
                    c['False'].append(ch['False'])
                else:
                    ch = count_ch(ch)
                    for label in counts:
                        c[label].append(ch[label])
    r = {'time': t, 'count': c}
    return jsonify(r)


@app.route('/speakers')
def speakers():
    from collections import defaultdict
    names = data_s.iloc[:, 0].values.tolist()
    name_dict = defaultdict(list)
    for n in names:
        name_dict[n[0].upper()].append(n)
    sorted_names = sorted(name_dict.items(), key=lambda x: x[0])
    return jsonify(sorted_names)


@app.route('/party')
def party():
    from collections import defaultdict
    parties = data_s.iloc[:, 1].values.tolist()
    parties = list(set(parties))
    party_dict = defaultdict(list)
    for p in parties:
        party_dict[p[0].upper()].append(p)
    sorted_party = sorted(party_dict.items(), key=lambda x: x[0])
    return jsonify(sorted_party)


if __name__ == '__main__':
    # 以后启动在 terminal里 python app.py
    app.run(host='0.0.0.0', port=5000, debug=True)
