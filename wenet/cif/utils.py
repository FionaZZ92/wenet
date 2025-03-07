# Copyright (c) 2023 ASLP@NWPU (authors: He Wang, Fan Yu)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License. Modified from
# FunASR(https://github.com/alibaba-damo-academy/FunASR)

from typing import Optional

import six
import torch
import numpy as np


def make_pad_mask(lengths: torch.Tensor, length_dim: int = -1,
                  maxlen: Optional[int] = None):
    """Make mask tensor containing indices of padded part.

    Args:
        lengths (LongTensor or List): Batch of lengths (B,).
        xs (Tensor, Optional)
        length_dim (int, optional): Dimension indicator of the above tensor.
            See the example.
        maxlen (int, optional)

    Returns:
        Tensor: Mask tensor containing indices of padded part.
                dtype=torch.uint8 in PyTorch 1.2-
                dtype=torch.bool in PyTorch 1.2+ (including 1.2)


    """
    if length_dim == 0:
        raise ValueError("length_dim cannot be 0: {}".format(length_dim))

    bs = lengths.size(0)
    if maxlen is None:
        maxlen = lengths.max()
    else:
        assert maxlen >= lengths.max().item()

    seq_range = torch.arange(0, maxlen, dtype=torch.int64)
    seq_range_expand = seq_range.unsqueeze(0).expand(bs, maxlen)
    seq_length_expand = lengths.unsqueeze(-1).to(seq_range_expand.device)
    mask = seq_range_expand >= seq_length_expand

    return mask


def sequence_mask(lengths, maxlen: Optional[int] = None,
                  dtype: torch.dtype = torch.float32,
                  device: Optional[torch.device] = None) -> torch.Tensor:
    if maxlen is None:
        maxlen = lengths.max()
    row_vector = torch.arange(0, maxlen, 1).to(lengths.device)
    matrix = torch.unsqueeze(lengths, dim=-1)
    mask = row_vector < matrix
    mask = mask.detach()

    return mask.type(dtype).to(device) if device is not None else \
        mask.type(dtype)


def end_detect(ended_hyps, i, M=3, d_end=np.log(1 * np.exp(-10))):
    """End detection.

    described in Eq. (50) of S. Watanabe et al
    "Hybrid CTC/Attention Architecture for End-to-End Speech Recognition"

    :param ended_hyps:
    :param i:
    :param M:
    :param d_end:
    :return:
    """
    if len(ended_hyps) == 0:
        return False
    count = 0
    best_hyp = sorted(ended_hyps, key=lambda x: x["score"], reverse=True)[0]
    for m in six.moves.range(M):
        # get ended_hyps with their length is i - m
        hyp_length = i - m
        hyps_same_length = [x for x in ended_hyps if
                            len(x["yseq"]) == hyp_length]
        if len(hyps_same_length) > 0:
            best_hyp_same_length = sorted(
                hyps_same_length, key=lambda x: x["score"], reverse=True)[0]
            if best_hyp_same_length["score"] - best_hyp["score"] < d_end:
                count += 1

    if count == M:
        return True
    else:
        return False
