from models.inverter import Inverter
from models.sbert import sbert
from models.stylegan_model import StyleGAN2
from models.text_encoder import TextEncoder
from models.latent_code_decoder import LatentCodeDecoder
from models.manipulater import LatentManipulator
from models.direction_classifier import DirectionClassifier
from utils.common import tensor2im
from utils.image_preprocess import image_preprocess
from configs.paths import get_path
import torch
import PIL.Image
import numpy as np
import sys
import traceback


class Model() :
    def __init__(self) :
        self.sbert = sbert(get_path('sbert'))

        self.inverter = Inverter()
        self.inverter.load_model(get_path('inversion'))

        self.stylegan = StyleGAN2()
        self.stylegan.load_model(get_path('stylegan2'))

        self.text_encoder = TextEncoder()
        self.text_encoder.load_model(get_path('text_encoder'))

        self.latent_code_decoder = LatentCodeDecoder()
        self.latent_code_decoder.load_model(get_path('latent_code_decoder'))
        
        self.direction_classifier = DirectionClassifier()
        self.direction_classifier.load_model(get_path('direction_classifier'))

        self.lantent_manipulator = LatentManipulator()
    
    def save_image(self,image,type_) :
        if(type_ == 'gen') :
            file_save_path = 'test/generated.jpg'
        elif(type_ == 'man') :
            file_save_path = 'test/manipulated.jpg'
        save_output_image = PIL.Image.fromarray(np.array(tensor2im(image)))
        save_output_image.save(file_save_path)
    
    def generate(self,text) :
        # Generates a image from text and saves it
        try :
            with torch.no_grad() :
                sentence_embedding = self.sbert.encode(text)
                attribute_vector = self.text_encoder(sentence_embedding)
                latent_code = self.latent_code_decoder(attribute_vector)
                latent_code = torch.reshape(latent_code,(1,18,512))
                generated_image = self.stylegan.generate(latent_code)
            self.save_image(generated_image,'gen')
        except Exception as e :
            print(traceback.format_exc())
            return False
        return True
    
    def manipulate(self, text, image_input_mode = 'last') :
        
        try :
            with torch.no_grad() :
                if image_input_mode == 'upload' :
                    image_path = 'test/input.jpg'
                elif image_input_mode == 'last' :
                    image_path = 'test/generated.jpg'
                preprocessed_image = image_preprocess(image_path)
                latent_code = self.inverter.invert(preprocessed_image)
                sentence_embedding = self.sbert.encode(text)
                label_proba = self.direction_classifier(sentence_embedding)
                attribute,effect = self.direction_classifier.get_label(label_proba)
                new_latent_code = self.lantent_manipulator.manipulate_latent(latent_code, attribute, effect)
                modified_image = self.stylegan.generate(new_latent_code)
            self.save_image(modified_image,'man')
        except Exception as e :
            print(traceback.format_exc())
            return False
        return True
