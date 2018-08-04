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
    with open('logs/g_translation.txt', 'r') as f:
        for line in f:
            i += 1
            if False: #(i > 5):
                break
            words = tokenize_line(line)
            for word in words:
                if(len(word) <= 15):
                    broken_word = run(word,dict)
                else:
                    broken_word = '%'+word+' '
                file.write(broken_word)
            file.write('\n')
    file.close()

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

dict = Dictionary.load('logs/dict.en.txt')

list_of_splits = []

iterator = 0

def next_word():

    global iterator

    if(iterator == len(list_of_splits)):
        return "<UNK>"
    current_word = list_of_splits[iterator]

    for i in range(len(current_word)-1,0,-1):

        split_possible = False
        if current_word[i] != ' ' and current_word[i-1] != ' ':
            new_word_to_append = current_word[:i] + ' ' + current_word[i:]
            split_possible = True

        if split_possible and not new_word_to_append in list_of_splits and new_word_to_append.count(' ') <= 5:
            list_of_splits.append(new_word_to_append)
            
    iterator += 1

    if iterator > len(list_of_splits):
        return "<UNK>"    
    else:
        return list_of_splits[iterator-1]

def run(word, dict):

    global list_of_splits, iterator

    list_of_splits = []
    iterator = 0    
    word.strip('\n')
    list_of_splits.append(word)
    
    print(word)
    while 1:
        check_word = next_word()
        if check_word != "<UNK>":
            list_of_current_word = check_word.split(' ')
            for j in range(len(list_of_current_word)-1):
                list_of_current_word[j] = list_of_current_word[j] + '@@'

            found_all_parts = True

            for j in range(len(list_of_current_word)):
                if not check(list_of_current_word[j],dict):
                    found_all_parts = False

            if found_all_parts:
                output = ''
                for sub_words in list_of_current_word:
                    output += sub_words + ' '

                return output
        else:
            y = '<UNK>' + word + ' '
            return y

remake_dict(dict)
