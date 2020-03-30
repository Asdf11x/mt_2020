"""
gru99_model.py:
https://www.guru99.com/seq2seq-model.html

"""

from __future__ import unicode_literals, division
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

import numpy as np
import pandas as pd
import random

import os
import re
import random

from torch.autograd import Variable

from Dataloader.text_to_kp.text_to_kps_dataset import TextKeypointsDataset
from Dataloader.text_to_kp.text_to_kps_dataset import ToTensor
import matplotlib.pyplot as plt
import torch
import torch.utils
import torch.utils.data

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Encoder(nn.Module):
    def __init__(self, input_dim, hidden_dim, embbed_dim, num_layers):
        super(Encoder, self).__init__()

        # set the encoder input dimesion , embbed dimesion, hidden dimesion, and number of layers
        self.input_dim = input_dim
        self.embbed_dim = embbed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # initialize the embedding layer with input and embbed dimention
        self.embedding = nn.Embedding(input_dim + 1, self.embbed_dim)
        # intialize the GRU to take the input dimetion of embbed, and output dimention of hidden and
        # set the number of gru layers
        self.gru = nn.GRU(self.embbed_dim, self.hidden_dim, num_layers=self.num_layers)

    def forward(self, src):
        embedded = self.embedding(src).view(1, 1, -1)
        outputs, hidden = self.gru(embedded)
        return outputs, hidden


class Decoder(nn.Module):
    def __init__(self, output_dim, hidden_dim, embbed_dim, num_layers):
        super(Decoder, self).__init__()

        # set the encoder output dimension, embed dimension, hidden dimension, and number of layers
        self.emb_dim = embbed_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers

        # initialize every layer with the appropriate dimension. For the decoder layer,
        # it will consist of an embedding, GRU, a Linear layer and a Log softmax activation function.
        self.embedding = nn.Embedding(output_dim, self.emb_dim)
        print(self.embedding)
        self.gru = nn.GRU(self.emb_dim, self.hidden_dim, num_layers=self.num_layers)
        print(self.gru)
        self.out = nn.Linear(self.hidden_dim, output_dim)
        self.softmax = nn.LogSoftmax(dim=1)

    def forward(self, input, hidden):
        # reshape the input to (1, batch_size)
        input = input.view(1, -1)
        embedded = F.relu(self.embedding(input))
        output, hidden = self.gru(embedded, hidden)
        prediction = self.softmax(self.out(output[0]))

        return prediction, hidden


class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder, device):
        super().__init__()

        # initialize the encoder and decoder
        self.encoder = encoder
        self.decoder = decoder
        self.device = device

    def forward(self, source, target, teacher_forcing_ratio=0.5):

        input_length = source.size(0)  # get the input length (number of words in sentence)
        batch_size = target.shape[1]
        target_length = target.shape[0]
        vocab_size = self.decoder.output_dim

        # initialize a variable to hold the predicted outputs
        outputs = torch.zeros(target_length, batch_size, vocab_size).to(self.device)

        # encode every word in a sentence
        for i in range(input_length):
            encoder_output, encoder_hidden = self.encoder(source[i])

        # use the encoder’s hidden layer as the decoder hidden
        decoder_hidden = encoder_hidden.to(device)

        # add a token before the first predicted word
        decoder_input = torch.tensor([SOS_token], device=device)  # SOS

        # topk is used to get the top K value over a list
        # predict the output word from the current target word. If we enable the teaching force,  then the #next decoder input is the next word, else, use the decoder output highest value.

        for t in range(target_length):
            decoder_output, decoder_hidden = self.decoder(decoder_input, decoder_hidden)
            outputs[t] = decoder_output
            teacher_force = random.random() < teacher_forcing_ratio
            topv, topi = decoder_output.topk(1)
            input = (target[t] if teacher_force else topi)
            if (teacher_force == False and input.item() == EOS_token):
                break

        return outputs


class RunModel:

    def init_model(self):
        # create encoder-decoder model
        encoder = Encoder(2, hidden_size, embed_size, num_layers)
        decoder = Decoder(6, hidden_size, embed_size, num_layers)
        model = Seq2Seq(encoder, decoder, device).to(device)
        return model

    def train_helper(self, model):
        model.train()
        model_optimizer = optim.SGD(model.parameters(), lr=0.01)
        criterion = nn.L1Loss()
        total_loss_iterations = 0

        for idx in range(1, num_iteration + 1):
            nexty = next(it)
            rnd = random.randint(20, 50)

            in_ten = torch.as_tensor(nexty[0], dtype=torch.long).view(-1, 1)
            out_ten = torch.as_tensor(nexty[1], dtype=torch.float).view(-1, 1)[:20]  # crop to 20 for testing
            print("in_ten.size: %d, out_ten.size: %d" % (in_ten.size()[0], out_ten.size()[0]))

            loss = run_model_own.train_own(model, in_ten, out_ten, model_optimizer, criterion)

            total_loss_iterations += loss

            if idx % 1 == 0:
                avarage_loss = total_loss_iterations / 1
                total_loss_iterations = 0
                print('Epoch %d, average loss: %.2f' % (idx, avarage_loss))

    # train
    def train_own(self, model, input_tensor, target_tensor, model_optimizer, criterion):
        model_optimizer.zero_grad()
        loss = 0.0
        output = model(input_tensor, target_tensor)
        num_iter = output.size(0)

        # calculate the loss from a predicted sentence with the expected result
        for ot in range(num_iter):
            # print("output %s, target %s" % (str(output.size()), str(target_tensor.size())))
            # print("output %s, target %s" % (str(output[ot].size()), str(target_tensor[ot].size())))
            # print(output)
            loss += criterion(output[ot], target_tensor[ot])
        loss.backward()
        model_optimizer.step()
        epoch_loss = loss.item() / num_iter

        # print(epoch_loss)
        return epoch_loss

    def evaluate_model_own(self):
        # evaluate (kommt nur scheisse raus)
        it = iter(keypoints_loader)
        nexty = next(it)

        with torch.no_grad():
            in_ten = torch.as_tensor(nexty[0], dtype=torch.long).view(-1, 1)
            out_ten = torch.as_tensor(nexty[1], dtype=torch.float).view(-1, 1)[:20]  # crop to 20 for testing
            print("in_ten.size: %d, out_ten.size: %d" % (in_ten.size()[0], out_ten.size()[0]))
            print("in_ten: %s, out_ten: %s" % (str(in_ten), str(out_ten)))
            print("---" * 9)
            decoded_words = []

            output = model(in_ten, out_ten)
            print("output.size: %d" % output.size(0))
            print(output)
            print("---" * 10)
            for ot in range(output.size(0)):
                topv, topi = output[ot].topk(1)

                print(topv)
                print(topi)

                if topi[0].item() == EOS_token:
                    decoded_words.append('<EOS>')
                    break
                else:
                    decoded_words.append(out_ten)
                # print(decoded_words)


if __name__ == '__main__':
    teacher_forcing_ratio = 0.5
    embed_size = 16
    hidden_size = 512
    num_layers = 1
    num_iteration = 3
    SOS_token = 0
    EOS_token = 1

    text2kp = TextKeypointsDataset(path_to_numpy_file="own_data_morse/all_files_normalized.npy",
                                   path_to_csv='own_data_morse/sentences.csv', transform=ToTensor())
    keypoints_loader = torch.utils.data.DataLoader(text2kp, batch_size=1, shuffle=True, num_workers=0)

    it = iter(keypoints_loader)
    run_model_own = RunModel()

    model = run_model_own.init_model()
    run_model_own.train_helper(model)

    run_model_own.evaluate_model_own()
