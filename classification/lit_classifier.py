

import torch
import torch.nn as nn
from config import CONFIG
from torch.nn import functional as F

import logging
from classification.metrics import get_metrics_collections_base,get_metric_AUROC
from classification.lit_system import LitSystem

class LitClassifier(LitSystem):
    def __init__(self,
                 model:nn.Module,
                 NUM_CLASSES,
                #   loss_fn=nn.CrossEntropyLoss(),
                  lr=CONFIG.lr,
                  optim:str="SGD"
                  
                  ):
        
        super().__init__( NUM_CLASSES,lr,optim)
        
        #puede que loss_fn no vaya aquí y aquí solo vaya modelo
        self.model=model
        for name,param in self.model.named_parameters():
            if param.requires_grad:
                print(name)
                
                
        self.criterion=F.cross_entropy
                
        a=self.parameters()
    def forward(self,x):
        x=self.model(x)
        
        return x 
    
    def on_epoch_start(self):
        torch.cuda.empty_cache()
    
    def training_step(self,batch,batch_idx):
        x,targets=batch
        preds=self.model(x)
        loss=self.criterion(preds,targets)

        if torch.any(torch.isnan(preds)):
            nan_mask=torch.any(torch.isnan(preds))
            logging.error((preds))
            print("tiene nan, averiguar")
            print( "resultado de softmax", nn.functional.softmax(preds,dim=1))
            logging.error(nn.functional.softmax(preds,dim=1))
            raise RuntimeError(f"Found NAN in output {batch_idx} at indices: ", nan_mask.nonzero(), "where:", x[nan_mask.nonzero()[:, 0].unique(sorted=True)])

        if isinstance(targets,list):
            targets=targets[0]
        
        #lo ideal sería hacer algo tipo loss,preds=self.model(x) de esta manera al modelo se le 
        #incluiria el loss fn y así podremos hacer la tripleta
        preds_probability=nn.functional.softmax(preds,dim=1)
        metric_value=self.train_metrics_base(preds_probability,targets)
        data_dict={"loss":loss,**metric_value}

        self.insert_each_metric_value_into_dict(data_dict,prefix="")

        
        return loss
    
    def validation_step(self, batch, batch_idx):
        x, targets = batch
        preds=self.model(x)
        loss=self.criterion(preds,targets)
   
        if isinstance(targets,list):
            targets=targets[0]
        preds_probability=nn.functional.softmax(preds,dim=1)
        metric_value=self.valid_metrics_base(preds_probability,targets)
        data_dict={"val_loss":loss,**metric_value}
  
        self.insert_each_metric_value_into_dict(data_dict,prefix="")
        