# based on https://github.com/pytorch/examples/tree/master/mnist
#%%
# %load_ext autoreload
# %autoreload 2

import argparse

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms

from raymon.external import FileLogger, APILogger
from raymon.ray import Ray

# ray = FileLogger(fpath='raymon.log', stdout=True, context="MNIST Example")
ray_api = APILogger(url="http://localhost:8000", context="MNIST Example", project_id="Testing")


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 20, 5, 1)
        self.conv2 = nn.Conv2d(20, 50, 5, 1)
        self.fc1 = nn.Linear(4*4*50, 500)
        self.fc2 = nn.Linear(500, 10)

    def forward(self, x, ray):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2, 2)
        ray.log_numpy(peephole='l1_features', data=np.squeeze(data.numpy(), 0))
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2, 2)
        ray.log_numpy(peephole='l2_features', data=np.squeeze(data.numpy(), 0))
        x = x.view(-1, 4*4*50)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        final = F.log_softmax(x, dim=1)
        return final



def process_ray(model, ray, data, target):
    model.eval()
    with torch.no_grad():
        output = model(data, ray=ray)
        pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
        correct = pred.eq(target.view_as(pred)).sum().item()
        return correct

#%%
device = 'cpu'
test_loader = torch.utils.data.DataLoader(
    datasets.MNIST(root='/Users/kv/Downloads/raymon_data/mnist', 
                   train=False, 
                   download=True,
                   transform=transforms.Compose([
                        transforms.ToTensor(),
                        transforms.Normalize((0.1307,), (0.3081,))  # TODO: Wrap callable
                    ])),
    batch_size=1, 
    shuffle=True)

model = Net().to(device)
for i, (data, target) in enumerate(test_loader):
    ray = Ray(logger=ray_api)
    # ray.log_id(ray_id)  # Will make sure the ray is registered.
    ray.log_text(peephole="Ingestion", data="Received new ray")
    ray.log_numpy(peephole='network_input',  data=np.squeeze(data.numpy(), 0))
    data, target = data.to(device), target.to(device)
    correct = process_ray(model, ray=ray, data=data, target=target)
    if i == 1:
        break

# %%
ray.log_text(peephole="Ingestion", data="Received new ray")


# %%
