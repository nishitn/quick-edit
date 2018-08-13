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
  --destdir data-bin/de-en
```

# Translate line-by-line
```translate.py``` translates line-by-line from your existing model and saves output in ```logs/translate.txt```

python3 generate.py data-bin/iwslt14.tokenized.de-en \
  --path checkpoints/fconv/checkpoint_best.pt \
  --batch-size 128 --beam 5

python3 interactive.py \
  --path checkpoints/fconv/checkpoint_best.pt checkpoints/fconv \
  --beam 5

CUDA_VISIBLE_DEVICES=0 python3 train.py data-bin/de-en/   --lr 0.25 --clip-norm 0.1 \
  --dropout 0.2 --max-tokens 40   --arch fconv_iwslt_de_en \
  --save-dir checkpoints/de-en --max-epoch 1
