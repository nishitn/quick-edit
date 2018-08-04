from googletrans import Translator
import os
translator = Translator()
file = open('logs/g_translation.txt','a')
i = 0

with open('data/iwslt14.tokenized.de-en/test.de', 'r') as f:
    for line in f:
        if(i < 6694):
            print(i, end='\r')
            i += 1
            continue
        elif(i < 7000):
            t=translator.translate(line, src='de', dest='en')
            try:
                file.write(t.text)
                file.write('\n')
                print(i,end='\r')
            except:
                file.write("errorerror ",i)
                file.write('\n')
                print(t.text)
                print(i)
            i += 1
        else:
            print('')
            break
file.close()
