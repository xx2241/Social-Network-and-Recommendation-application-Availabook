f = open('LDA.txt',"w")

f2 = open('LDA_raw.txt', 'r')
for sentence in f2:
    prefixes = ('RT', 'http', '@')
    list = sentence.split(' ')
    for word in list[:]:
        if word.startswith(prefixes):
            list.remove(word)
    str = ' '.join(list)
    f.write(str)