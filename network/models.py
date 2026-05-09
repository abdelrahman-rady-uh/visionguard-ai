# Shim — recreates TransferModel so FaceForensics++ .p files can be unpickled
import torch
import torch.nn as nn
from network.xception import Xception, xception


class TransferModel(nn.Module):
    """Minimal replica of the FaceForensics++ TransferModel for pickle compatibility."""
    def __init__(self, modelchoice="xception", num_out_classes=2, dropout=0.0):
        super().__init__()
        self.modelchoice = modelchoice
        self.model = xception(pretrained=False)
        num_ftrs = self.model.last_linear.in_features
        if dropout:
            self.model.last_linear = nn.Sequential(
                nn.Dropout(p=dropout),
                nn.Linear(num_ftrs, num_out_classes),
            )
        else:
            self.model.last_linear = nn.Linear(num_ftrs, num_out_classes)

    def forward(self, x):
        return self.model(x)
