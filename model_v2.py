# -*- coding: utf-8 -*-
"""
Created on Sun Jun 17 07:54:53 2018

@author: 北海若
"""

import keras
from keras import layers
import numpy as np


N_CLASS = 45


def key_to_category(key, one_hot=True, new=False):
    cws = 0
    cad = 0
    cjkld = 0
    if key & 1 > 0:  # W
        cws = 1
    if key & 2 > 0:
        cws = 2
    if key & 4 > 0:
        cad = 1
    if key & 8 > 0:
        cad = 2
    if key & 64 > 0:
        cjkld = 3
    if key & 128 > 0:
        cjkld = 4
    if key & 16 > 0:
        cjkld = 1
    if key & 32 > 0:
        cjkld = 2
    if new:
        return np.eye(5)[cjkld], np.eye(3)[cad], np.eye(3)[cws]
    elif one_hot:
        return np.eye(N_CLASS)[cjkld * 9 + cad * 3 + cws]
    else:
        return cjkld * 9 + cad * 3 + cws


def encode_keylist(list_key, merge=1, one_hot=True, new=False):
    list_key = list_key.copy()
    tmp = []
    for i in range(len(list_key)):
        list_key[i] = key_to_category(list_key[i], one_hot=one_hot, new=new)
    for i in range(0, len(list_key), merge):
        tmp.append(list_key[i])
    list_key = tmp
    '''for i in range(merge):
        for j in range(len(list_key)):
            if j > 0 and list_key[j] == list_key[j - 1]:
                continue
            tmp.append(list_key[j])
        list_key = tmp
        tmp = []'''
    return np.array(list_key)


def attention_3d_block(inputs):
    a = layers.Permute((2, 1))(inputs)
    a = layers.Dense(30, activation='softmax')(a)
    a_probs = layers.Permute((2, 1))(a)
    output_attention_mul = layers.Multiply()([inputs, a_probs])
    return output_attention_mul


def conv1d_block(*args, **kwargs):
    def conv1d_get_tensor(inputs):
        x = layers.Conv1D(*args, **kwargs)(inputs)
        x = layers.LeakyReLU()(x)
        x = layers.BatchNormalization()(x)
        return x
    return conv1d_get_tensor


def wavenet_block(n_atrous_filters, atrous_filter_size, atrous_rate):
    def f(input_):
        residual = input_
        tanh_out = layers.Conv1D(n_atrous_filters, atrous_filter_size,
                                 dilation_rate=atrous_rate,
                                 padding='causal',
                                 activation='tanh')(input_)
        sigmoid_out = layers.Conv1D(n_atrous_filters, atrous_filter_size,
                                    dilation_rate=atrous_rate,
                                    padding='causal',
                                    activation='sigmoid')(input_)
        merged = layers.Multiply()([tanh_out, sigmoid_out])
        merged = layers.BatchNormalization()(merged)
        skip_out = layers.Conv1D(64, 1)(merged)
        skip_out = layers.LeakyReLU()(skip_out)
        skip_out = layers.BatchNormalization()(skip_out)
        out = layers.Add()([skip_out, residual])
        return out, skip_out
    return f


def get_model():
    char_action = layers.Input(shape=[30, 4])
    char_action_a = attention_3d_block(char_action)

    position = layers.Input(shape=[6])
    position_r = layers.RepeatVector(30)(position)

    enemy_key = layers.Input(shape=[30, 45])
    enemy_key_a = attention_3d_block(enemy_key)

    my_key = layers.Input(shape=[30, 45])
    my_key_a = attention_3d_block(my_key)
    concat = layers.Concatenate()([char_action_a, position_r,
                                   enemy_key_a, my_key_a])
    gate = layers.Dense(100, activation="sigmoid")(concat)
    concat = layers.Multiply()([gate, concat])
    '''flatten = layers.Flatten()(concat)
    dense = layers.Dense(128, activation="tanh")(flatten)
    c = layers.Dense(128, activation="tanh")(dense)
    c = layers.Dense(128, activation="tanh")(c)'''
    first = conv1d_block(64, 5, padding='causal', activation='tanh')(concat)
    A, B = wavenet_block(64, 2, 1)(first)
    skip_connections = [B]
    for i in range(1, 12):
        A, B = wavenet_block(64, 3, 2 ** (i % 3))(A)
        skip_connections.append(B)
    net = layers.Add()(skip_connections)
    net = layers.LeakyReLU()(net)
    net = conv1d_block(12, 1)(net)
    net = layers.LeakyReLU()(net)
    c = layers.Flatten()(net)
    dense_category = layers.Dense(45, activation='softmax')(c)
    return keras.models.Model(inputs=[char_action,
                                      position,
                                      enemy_key,
                                      my_key],
                              outputs=[dense_category],
                              name="TH123AI")
