#!/usr/bin/env python3 -u
# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the LICENSE file in
# the root directory of this source tree. An additional grant of patent rights
# can be found in the PATENTS file in the same directory.

import torch
import numpy
from fairseq import bleu, data, options, progress_bar, tokenizer, utils
from fairseq.meters import StopwatchMeter, TimeMeter
from fairseq.sequence_generator import SequenceGenerator
from fairseq.sequence_scorer import SequenceScorer
from nltk.translate.bleu_score import sentence_bleu


def main(args):
    assert args.path is not None, '--path required for generation!'
    print(args)
    assert not args.sampling or args.nbest == args.beam, \
        '--sampling requires --nbest to be equal to --beam'

    use_cuda = torch.cuda.is_available() and not args.cpu

    # Load dataset
    if args.replace_unk is None:
        dataset = data.load_dataset(
            args.data,
            [args.gen_subset],
            args.source_lang,
            args.target_lang,
        )
    else:
        dataset = data.load_raw_text_dataset(
            args.data,
            [args.gen_subset],
            args.source_lang,
            args.target_lang,
        )
    if args.source_lang is None or args.target_lang is None:
        # record inferred languages in args
        args.source_lang, args.target_lang = dataset.src, dataset.dst

    # Load ensemble
    print('| loading model(s) from {}'.format(', '.join(args.path)))
    models, _ = utils.load_ensemble_for_inference(args.path, dataset.src_dict, dataset.dst_dict)

    print('| [{}] dictionary: {} types'.format(dataset.src, len(dataset.src_dict)))
    print('| [{}] dictionary: {} types'.format(dataset.dst, len(dataset.dst_dict)))
    print('| {} {} {} examples'.format(args.data, args.gen_subset, len(dataset.splits[args.gen_subset])))

    # Optimize ensemble for generation
    for model in models:
        model.make_generation_fast_(
            beamable_mm_beam_size=None if args.no_beamable_mm else args.beam,
        )

    # Load alignment dictionary for unknown word replacement
    # (None if no unknown word replacement, empty if no path to align dictionary)
    align_dict = utils.load_align_dict(args.replace_unk)

    # Load dataset (possibly sharded)
    max_positions = min(model.max_encoder_positions() for model in models)
    itr = dataset.eval_dataloader(
        args.gen_subset,
        max_sentences=args.max_sentences,
        max_positions=max_positions,
        skip_invalid_size_inputs_valid_test=True,
    )
    if args.num_shards > 1:
        if args.shard_id < 0 or args.shard_id >= args.num_shards:
            raise ValueError('--shard-id must be between 0 and num_shards')
        itr = data.sharded_iterator(itr, args.num_shards, args.shard_id)

    # Initialize generator
    gen_timer = StopwatchMeter()
    if args.score_reference:
        translator = SequenceScorer(models)
    else:
        translator = SequenceGenerator(
            models, beam_size=args.beam, stop_early=(not args.no_early_stop),
            normalize_scores=(not args.unnormalized), len_penalty=args.lenpen,
            unk_penalty=args.unkpen, sampling=args.sampling)
    if use_cuda:
        translator.cuda()

    # Generate and compute BLEU score
    scorer = bleu.Scorer(dataset.dst_dict.pad(), dataset.dst_dict.eos(), dataset.dst_dict.unk())
    check = [] #------------------------------------------------------------------------------------------------------
    num_sentences = 0
    has_target = True
    with progress_bar.build_progress_bar(args, itr) as t:
        if args.score_reference:
            translations = translator.score_batched_itr(t, cuda=use_cuda, timer=gen_timer)
        else:
            translations = translator.generate_batched_itr(
                t, maxlen_a=args.max_len_a, maxlen_b=args.max_len_b,
                cuda=use_cuda, timer=gen_timer, prefix_size=args.prefix_size)
        wps_meter = TimeMeter()
        for sample_id, src_tokens, guess_tokens, target_tokens, hypos, marker in translations:
            # Process input and ground truth
            has_target = target_tokens is not None
            target_tokens = target_tokens.int().cpu() if has_target else None
            # Either retrieve the original sentences or regenerate them from tokens.
            if align_dict is not None:
                src_str = dataset.splits[args.gen_subset].src.get_original_text(sample_id)
                guess_str = dataset.splits[args.gen_subset].guess.get_original_text(sample_id)
                target_str = dataset.splits[args.gen_subset].dst.get_original_text(sample_id)
            else:
                src_str = dataset.src_dict.string(src_tokens, args.remove_bpe)
                guess_str = dataset.dst_dict.string(guess_tokens, args.remove_bpe, escape_unk=True)
                target_str = dataset.dst_dict.string(target_tokens,
                                                     args.remove_bpe,
                                                     escape_unk=True) if has_target else ''
            if not args.quiet:
                #print('S-{}\t{}'.format(sample_id, src_str))
                if has_target:
                    y = str(sample_id.cpu().numpy()) + ' T= ' + str(target_str) + '\n'
                    detailed_file.write(y)
                    
                    print('G-{}\t{}'.format(sample_id, guess_str))
                    print('T-{}\t{}'.format(sample_id, target_str))
                else:
                    y=str(sample_id.cpu().numpy())+'checkcheck\n'
                    detailed_file.write(y)
            # Process top predictions
            for i, hypo in enumerate(hypos[:min(len(hypos), args.nbest)]):
                hypo_tokens, hypo_str, alignment = utils.post_process_prediction(
                    hypo_tokens=hypo['tokens'].int().cpu(),
                    src_str=src_str,
                    alignment=hypo['alignment'].int().cpu(),
                    align_dict=align_dict,
                    dst_dict=dataset.dst_dict,
                    remove_bpe=args.remove_bpe,
                )

                if not args.quiet:
                    print('H-{}\t{}\t{}'.format(sample_id, hypo['score'], hypo_str))
                    
                    guess_score = get_bleu(target_str, remove_pad(guess_str)) 
                    hypo_score = get_bleu(target_str, hypo_str)
                    check.append(hypo_score)
                    guess_str = make_bold(guess_str, marker)

                    y = str(sample_id.cpu().numpy()) + ' ' + str(guess_score) + ' G= ' + str(guess_str) + '\n'
                    detailed_file.write(y)
                    y = str(sample_id.cpu().numpy()) + ' ' + str(hypo_score) + ' H= ' + str(hypo_str) + '\n'
                    detailed_file.write(y)

#                   print('P-{}\t{}'.format( sample_id, ' '.join(map(
#                            lambda x: '{:.4f}'.format(x),
#                            hypo['positional_scores'].tolist(),
#                        ))
#                    ))
#                    print('A-{}\t{}'.format(
#                        sample_id,
#                        ' '.join(map(lambda x: str(utils.item(x)), alignment))
#                           ))

                # Score only the top hypothesis
                if has_target and i == 0:
                    if align_dict is not None or args.remove_bpe is not None:
                        # Convert back to tokens for evaluation with unk replacement and/or without BPE
                        target_tokens = tokenizer.Tokenizer.tokenize(
                            target_str, dataset.dst_dict, add_if_not_exist=True)
                    scorer.add(target_tokens, hypo_tokens)

            wps_meter.update(src_tokens.size(0))
            t.log({'wps': round(wps_meter.avg)})
            num_sentences += 1

    print('| Translated {} sentences ({} tokens) in {:.1f}s ({:.2f} tokens/s)'.format(
        num_sentences, gen_timer.n, gen_timer.sum, 1. / gen_timer.avg))
    summ = 0
    if has_target:
        for i in check:
            summ +=i
        summ = summ/len(check)
        print('| Check BLEU =', summ)
        print('| Generate {} with beam={}: {}'.format(args.gen_subset, args.beam, scorer.result_string()))


def make_bold(guess_str, marker):
    guess_array = guess_str.split(' ')
    guess_str = ''

    for i in range (marker.size(0) - 1):
        if(marker[i] == 1):
            guess_str += '<b>' + guess_array[i] + '</b> '
        else:
            guess_str += guess_array[i] + ' '

    return guess_str

def remove_pad(guess_str):
    guess_array = guess_str.split(' ')
    guess_str = ''
    for word in guess_array:
        if(word == '<pad>'):
            continue
        guess_str += word + ' '

    return guess_str

def get_bleu(ref, can):
    reference = [ref.split(' ')]
    candidate = can.split(' ')
#    print(reference, candidate, end = ' ')
    score = sentence_bleu(reference, candidate)
    score = numpy.around(score, decimals = 5)
    return score

if __name__ == '__main__':
    parser = options.get_generation_parser()
    args = parser.parse_args()
    detailed_file = open('logs/detailed_data.txt', 'a') #-----------------------------------------------------------------------------------
    main(args)
    detailed_file.close()
