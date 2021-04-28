#check this https://stackoverflow.com/questions/64607182/vs-code-remote-ssh-how-to-allow-processes-to-keep-running-to-completion-after-d
import datetime
import logging
# os.environ["PYTHONPATH"] ='/home/dcast/object_detection_TFM'
import sys
sys.path.append("/home/dcast/object_detection_TFM")
import pytorch_lightning as pl
import torch
import wandb
from config import CONFIG
from pytorch_lightning.callbacks import LearningRateMonitor
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from pytorch_lightning.callbacks.model_checkpoint import ModelCheckpoint
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.plugins import DDPPlugin

from classification.callback import ConfusionMatrix_Wandb
from classification.choice_loader import choice_loader_and_splits_dataset,Dataset
from classification.configs_experiments import ExperimentNames, get_config
from classification.lit_system import LitSystem
from classification.model.build_model import build_model

def main():
    print("empezando experimento")
    torch.backends.cudnn.benchmark = True
    experiment=ExperimentNames.TorchSqueezeNetDefaultLoss
    config_experiment=get_config(experiment,model_pretrained=False)
    dataset=Dataset.cars196
    wandb_logger = WandbLogger(project='TFM-classification',
                                entity='dcastf01',
                                name=experiment.name+" "+
                                datetime.datetime.utcnow().strftime("%Y-%m-%d %X"),
                            #    offline=True, #to debug
                                config={
                                    "batch_size":CONFIG.BATCH_SIZE,
                                    "num_workers":CONFIG.NUM_WORKERS,
                                    "experimentName":experiment.name,
                                    "lr":CONFIG.LEARNING_RATE,
                                    "use_TripletLoss":config_experiment.use_tripletLoss,
                                    "dataset":dataset.name,
                                    "backen cudnn benchmark":torch.backends.cudnn.benchmark,
                                    "pretrained_model":config_experiment.pretrained,
                                    }
                            
                               )
    
    dataloaders,NUM_CLASSES=choice_loader_and_splits_dataset(dataset,
                                                BATCH_SIZE=CONFIG.BATCH_SIZE,
                                                NUM_WORKERS=CONFIG.NUM_WORKERS,
                                                use_tripletLoss=config_experiment.use_tripletLoss
                                                )
    
    logging.info("DEVICE",CONFIG.DEVICE)
    train_loader=dataloaders["train"]
    test_loader=dataloaders["test"]
    
    # loss_fn = nn.CrossEntropyLoss()

    ##callbacks
    early_stopping=EarlyStopping(monitor='_val_loss',verbose=True)
    checkpoint_callback = ModelCheckpoint(
        monitor='_val_loss',
        dirpath=CONFIG.PATH_CHECKPOINT,
        filename= '-{epoch:02d}-{val_loss:.6f}',
        mode="min",
        save_last=True,
        save_top_k=3,
                        )
    learning_rate_monitor=LearningRateMonitor(logging_interval="epoch")
    
    # confusion_matrix_wandb=ConfusionMatrix_Wandb(list(range(CONFIG.NUM_CLASSES)))
        
    backbone=build_model(   architecture_name=config_experiment.architecture_name,
                            use_defaultLoss=config_experiment.use_defaultLoss,
                            use_tripletLoss=config_experiment.use_tripletLoss,
                            NUM_CLASSES=NUM_CLASSES
                            
                        )
    model=LitSystem(backbone,
                    # loss_fn=loss_fn,
                    lr=CONFIG.LEARNING_RATE,
                    NUM_CLASSES=NUM_CLASSES
                    )
    wandb_logger.watch(model.model)
    trainer=pl.Trainer(
                        logger=wandb_logger,
                       gpus=-1,
                       max_epochs=CONFIG.NUM_EPOCHS,
                       precision=16,
                    #    limit_train_batches=0.1, #only to debug
                    #    limit_val_batches=0.05, #only to debug
                    #    val_check_interval=1,
                    
                       log_gpu_memory=True,
                       distributed_backend='ddp',
                       accelerator="dpp",
                       plugins=DDPPlugin(find_unused_parameters=False),
                       callbacks=[
                            # early_stopping ,
                            checkpoint_callback,
                            # confusion_matrix_wandb,
                            learning_rate_monitor 
                                  ],
                       progress_bar_refresh_rate=50,
                       )
    logging.info("empezando el entrenamiento")
    trainer.fit(model,train_loader,test_loader)
         

if __name__ == "__main__":

    main()
