import contextlib
import itertools
import glob
import math
import numbers
import numpy as np
import os
import torch
import torch.utils.data

from fairseq.dictionary import Dictionary
from fairseq.indexed_dataset import IndexedDataset, IndexedInMemoryDataset, IndexedRawTextDataset
from fairseq import utils
from collections import Counter
import re

def remake_dict(dict):
    i=0
    file = open('logs/remake.txt', 'a')
    with open('data/iwslt14.tokenized.de-en/test.en', 'r') as f:
        for line in f:
            i+=1
            if(i>5):
                break
            words = tokenize_line(line)
            for word in words:
                
                if(check(word,dict)):
                    file.write(word)
                    file.write(' ')
                    continue
                else:
                    print(word)
                    a, b = find_subword(word, dict)
                    if b is None:
                        a, b= three_sub_words(word, dict)
                    y = a+' '+b+' '
                    print(y)
                    file.write(y)
            file.write('\n')
    file.close

SPACE_NORMALIZER = re.compile("\s+")
def tokenize_line(line):
    line = SPACE_NORMALIZER.sub(" ", line)
    line = line.strip()
    return line.split()

def check(word,dict):
    idx = dict.index(word)
    if(idx==3):
        return False
    else:
        return True

def three_sub_words(word,dict):
    l=len(word)
    while(l>0):
        a = word[:l-1] + '@@'
        b = word[l-1:]
        if(check(a, dict)):
            b, c = find_subword(b, dict)
            if c is not None:
                b = b+' '+c
                break
        l-=1
    if(l==0):
    	print('OHHHHHHHHH')
    	a=word
    	b='OHhhh'
    return a, b


def find_subword(word, dict):
    l=len(word)
    while(l>0):
        a = word[:l-1] + '@@'
        b = word[l-1:]
        if(check(a,dict) and check(b,dict)):
            break
        l-=1
    if(l==0):
    	a=None
    	b=None    
    return a, b

dict = Dictionary.load('data-bin/iwslt14.tokenized.de-en/dict.en.txt')
remake_dict(dict)