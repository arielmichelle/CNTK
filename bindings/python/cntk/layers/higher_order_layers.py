﻿# ==============================================================================
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

# higher_order_functions -- higher-order functions, like Sequential() and Recurrence()

from ..utils import Record
from .blocks import *
from .blocks import _initializer_for, _get_initial_state_or_default, _INFERRED, _inject_name
from . import sequence # they are also higher-order functions


def Sequential(layers, name=''):
    '''
    Layer factory function to create a composite that applies a sequence of layers (or any functions) onto an input.
    Sequential ([F, G, H]) === F >> G >> H
    '''
    if not isinstance(layers, list): # to support nested lists, run every item recursively through Sequential()
        # TODO: Is this confusing w.r.t. tuple which is parallel and list which is sequential?
        return layers
    from functools import reduce
    layers = [Sequential(layer) for layer in layers] # expand all layers recursively
    composed_function = reduce(lambda f, g: f >> g, layers, identity)

    composed_function = _inject_name(composed_function, name)

    # TODO: wrap this in a BlockFunction as to enforce inputs = inputs of first function
    return Block(composed_function, 'Sequential', Record(layers=layers))


def For(range, constructor, name=''):
    '''
    Layer factory function to create a composite that applies a sequence of layers constructed with a constructor lambda(layer).
    E.g.
     For(range(3), lambda i: Dense(2000))
     For(range(3), lambda: Dense(2000))
    '''
    #from inspect import signature
    #takes_arg = len(signature(constructor).parameters) > 0
    # Python 2.7 support requires us to use getargspec() instead
    from inspect import getargspec
    takes_arg = len(getargspec(constructor).args) > 0
    # helper to call the layer constructor
    def call(i):
        if takes_arg:
            return constructor(i)  # takes an arg: pass it
        else:
            return constructor()   # takes no arg: call without, that's fine too
    layers = [call(i) for i in range]
    sequential = Sequential(layers)

    sequential = _inject_name(sequential, name)

    return Block(sequential, 'For', Record(layers=layers))


# TODO: It is hard to find a good name for this.
def SequentialClique(functions, name=''):
    '''
    Layer factory function to create a composite that applies a sequence of or any functions onto an input,
    with skip connections between all function. I.e. each function receives a sum of the input and all
    prior functions' outputs.
    '''
    def clique(x):
        for f in functions:
            out = f(x)
            x = x + out
        return out

    clique = _inject_name(clique, name)

    return clique


# TODO: consider potential name clash; users might want to call their functions the same.
def ResNetBlock(f, name=''):
    '''
    Layer factory function to create a composite that adds a skip connection to a function.
    This is equivalent to ``SequentialClique([f, identity])``.
    '''
    def skip(x):
        return f(x) + x

    skip = _inject_name(skip, name)

    return skip


# legacy name--remove
def LayerStack(N, constructor):
    return For(range(N), constructor)
