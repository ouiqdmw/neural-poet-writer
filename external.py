# step 1
import torch
import matplotlib.pyplot as plt
import numpy as np 
import argparse
import pickle 
import os
from torch.autograd import Variable 
from torchvision import transforms 
from image_caption.build_vocab import Vocabulary
from image_caption.model import EncoderCNN, DecoderRNN
from PIL import Image
# step 2
from rnn.model import *
from rnn.train import *
from rnn.predict import *
from utils.code_book import code_book
from utils.data_cutter import data_cutter

def to_var(x, volatile=False):
    if torch.cuda.is_available():
        x = x.cuda()
    return Variable(x, volatile=volatile)
def load_image(image_path, transform=None):
    image = Image.open(image_path)
    image = image.resize([224, 224], Image.LANCZOS)
    
    if transform is not None:
        image = transform(image).unsqueeze(0)
    
    return image
def image_to_caption(image_file,  embed_size=256, hidden_size=512, num_layers=1):
    encoder_path = './image_caption/models/encoder-5-3000.pkl'
    decoder_path = './image_caption/models/decoder-5-3000.pkl'
    vocab_path = './image_caption/data/vocab.pkl'

    # Image preprocessing
    transform = transforms.Compose([
        transforms.ToTensor(), 
        transforms.Normalize((0.485, 0.456, 0.406), 
                             (0.229, 0.224, 0.225))])
    
    # Load vocabulary wrapper
    with open(vocab_path, 'rb') as f:
        vocab = pickle.load(f)

    # Build Models
    encoder = EncoderCNN(embed_size)
    encoder.eval()  # evaluation mode (BN uses moving mean/variance)
    decoder = DecoderRNN(embed_size, hidden_size, 
                         len(vocab), num_layers)
    

    # Load the trained model parameters
    encoder.load_state_dict(torch.load(encoder_path))
    decoder.load_state_dict(torch.load(decoder_path))

    # Prepare Image
    image = load_image(image_file, transform)
    image_tensor = to_var(image, volatile=True)
    
    # If use gpu
    if torch.cuda.is_available():
        encoder.cuda()
        decoder.cuda()
    
    # Generate caption from image
    feature = encoder(image_tensor)
    sampled_ids = decoder.sample(feature)
    sampled_ids = sampled_ids.cpu().data.numpy()
    
    # Decode word_ids to words
    sampled_caption = []
    for word_id in sampled_ids:
        word = vocab.idx2word[word_id]
        sampled_caption.append(word)
        if word == '<end>':
            break
    sentence = ' '.join(sampled_caption)

    return sentence

def caption_to_poem(start_str):
    # Make Codebook
    codebook_dir = "mid_data/"
    codebook_name = "code_set.txt"
    cb = code_book(codebook_dir)
    cb.load_from(codebook_name)

    # Load Trained Model
    model_dir = "rnn_models/"
    model_name = "rnn_model_result_final.pt"
    decoder = torch.load(model_dir + model_name)

    # process caption
    #dc = data_cutter('control_data')
    #start_str = data_cut(start_str)
    start_str = start_str.split('<')[1].split('>')[1]

    # Generate poem using rnn model
    start_sequence = cb.get_number_batch(start_str)
    poem = predict(decoder, start_sequence, 1000)

    return cb.get_string(poem)

def image_to_poem(image_file):
    caption = image_to_caption(image_file)
    poem = caption_to_poem(caption)
    return poem

