# text-post-edit
Using Facebooks fairseq library for a project
Link to Original -  [fairseq github](https://github.com/pytorch/fairseq/)

# Pre Processing

Pre-Porcess binarises guess file now, no extra code 
file name format = train.target_lang.guess test.target_lang.guess valid.target_lang.guess
Preprocess Code Example
```
python3 preprocess.py --source-lang de --target-lang en \
  --trainpref data/iwslt14.tokenized.de-en/train --validpref data/iwslt14.tokenized.de-en/valid --testpref data/iwslt14.tokenized.de-en/test \
  --destdir data-bin/iwslt14.tokenized.de-en
```

# Translate line-by-line
```translate.py``` translates line-by-line from your existing model and saves output in ```logs/translate.txt```

python3 generate.py data-bin/iwslt14.tokenized.de-en \
  --path checkpoints/fconv/checkpoint_best.pt \
  --batch-size 128 --beam 5