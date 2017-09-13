# Please install by typing the following command:
# 'python -m nltk.downloader -d /usr/share/nltk_data wordnet'
#
# If the corpora data can't be downloaded directly to the /usr/share/nltk_data folder
# error reports "no permission", please do:
# 1. Download the corpora to any directory you have the access to.
# `python -m nltk.downloader -d some_user_accessable_directory wordnet'
# 2. Add path to nltk path. In py file, add following lines:
import nltk
import operator

nltk.data.path.append('./nltk_data/')

from nltk.corpus import wordnet as wn


def get_score(w1, w2):
    dict = {}
    for i in w2:
        for j in w1:
            scores = []
            s1 = wn.synsets(j)
            s2 = wn.synsets(i)
            for x in s1:
                for y in s2:
                    if x.wup_similarity(y) is not None:
                        scores.append(x.wup_similarity(y))
            if len(scores) != 0:
                dict[i + "," + j] = max(scores)
    dict_sorted = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)
    print dict_sorted
    return dict_sorted[0][1]


w1 = [["love", "moive", "sport", "swim", "happy"],["study", "library", "computer", "read", "book"]]
data = "Come and join our summer football this Saturday!"
w2 = [w.lower() for w in data.replace('!', ' ').split(' ')]
similarity = []
for i in range(0,2):
    similarity.append(get_score(w1[i], w2))
print similarity
max_index, max_value = max(enumerate(similarity), key=operator.itemgetter(1))
cluster = max_index
print cluster
