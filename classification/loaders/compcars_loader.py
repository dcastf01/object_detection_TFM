import os
import random

import numpy as np
import pandas as pd
import torch
import torchvision.transforms as transforms
from classification.augmentation import get_transform_from_aladdinpersson
from classification.loaders.loader import Loader
from config import CONFIG
from dataset.compcars.compcar_analisis import CompcarAnalisis
from PIL import Image
from utils_visualize import plot_examples


class CompcarLoaderBasic(Loader):
    def __init__(self, df:pd.DataFrame,root_dir_images:str,
                  transform=None,condition_filter:str=None,is_train:bool=False):
        df=self.generate_label_id_on_df(df)
        super().__init__(df=df,root_dir_images=root_dir_images,
                         transform=transform,condition_filter=condition_filter,
                         is_train=is_train)
        
    def generate_label_id_on_df(self,df:pd.DataFrame)->dict:
            df['id'] = df.groupby(["make_id",'model_id','released_year']).ngroup()
        
            return df
    def _get_image_and_label(self,index):    
    
        def get_relative_path_img(index):

            return self.data.iloc[index]["Filepath"]
        def cut_car(image,index):
            X=self.data.iloc[index]["X"]
            Y=self.data.iloc[index]["Y"]

            w=self.data.iloc[index]["Width"]
            h=self.data.iloc[index]["Height"]
            
            return transforms.functional.crop(image,Y,X,h,w)
    
        img_path=os.path.join(self.root_dir_images,get_relative_path_img(index))
        image_global=Image.open(img_path).convert("RGB")
        image=np.array(cut_car(image_global,index))
    
        label=torch.tensor(int(self.data.iloc[index]["id"]))
        # label= torch.nn.functional.one_hot(label,num_classes=config.NUM_CLASSES)
        
        if self.transform:
            augmentations = self.transform(image=image)
            image = augmentations["image"]

        return image,label

    def __getitem__ (self,index):
        NotImplementedError
        
class CompcarLoader(CompcarLoaderBasic):
    def __init__(self, df:pd.DataFrame,root_dir_images:str,
                  transform=None,condition_filter:str=None,is_train:bool=False):
        super(CompcarLoader,self).__init__(df,root_dir_images,
                                            transform,condition_filter,
                                            is_train=is_train)
    
    def __getitem__ (self,index):
        image,label=self._get_image_and_label(index)
        return image,label
    
class CompcarLoaderTripletLoss(CompcarLoaderBasic):
    def __init__(self, df:pd.DataFrame,root_dir_images:str,
                  transform=None,condition_filter:str=None,is_train:bool=False):
        
        super(CompcarLoaderTripletLoss,self).__init__(df,root_dir_images,
                                            transform,condition_filter,
                                            is_train=is_train)
        self.is_train=is_train
                
        self.labels=(self.data.id.to_numpy())
        self.labels_set = set(self.data.id.to_numpy())
        self.label_to_indices = {label: np.where(np.array(self.labels) == label)[0]
                                     for label in self.labels_set}
        self.index=list(self.data.index.values)
        
    def __getitem__(self,index):
        
        anchor_img,anchor_label=self._get_image_and_label(index)
        #https://www.kaggle.com/hirotaka0122/triplet-loss-with-pytorch
        #https://github.com/adambielski/siamese-triplet/blob/master/datasets.py
        
        if self.is_train:
            positive_index=index
            while positive_index == index:
                # positive_list=self.index[self.index!=index][self.labels[self.index!=index]==anchor_label]
                positive_index = np.random.choice(self.label_to_indices[anchor_label.item()])
            
            negative_label=np.random.choice(list(self.labels_set-set([anchor_label.item()])))
            negative_index=np.random.choice(self.label_to_indices[negative_label])            
            # 
            # positive_index = random.choice(positive_list)
            
            positive_img,positive_label=self._get_image_and_label(positive_index)
            negative_img,negative_label=self._get_image_and_label(negative_index)
            
            return (anchor_img, positive_img, negative_img),(anchor_label,positive_label,negative_label)
        else:
            return anchor_img,anchor_label

def test_CompcarLoader():
    
    compcar_analisis=CompcarAnalisis(path_csv=config.PATH_COMPCAR_CSV)
    # compcar_analisis.filter_dataset('viewpoint=="4" or viewpoint=="1"')
    print(compcar_analisis.data.head())
    transform_train=get_transform_from_aladdinpersson()["train"]
    loader=CompcarLoader(compcar_analisis.data,
                         root_dir_images=config.PATH_COMPCAR_IMAGES,
                         transform=transform_train,
                         condition_filter=compcar_analisis.filter)
    images=[]
    for i in range(15):
        image,label=loader[0]
        images.append(image.permute(1, 2, 0))
    
    plot_examples(images)
    
# test_CompcarLoader()
