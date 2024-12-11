# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
import torch
from torch import nn
from torch.nn import functional as F

from maskrcnn_benchmark.modeling import registry
from maskrcnn_benchmark.modeling.backbone import resnet
from maskrcnn_benchmark.modeling.poolers import Pooler
from maskrcnn_benchmark.modeling.make_layers import group_norm
from maskrcnn_benchmark.modeling.make_layers import make_fc


@registry.ROI_BOX_FEATURE_EXTRACTORS.register("ResNet50Conv5ROIFeatureExtractor")
class ResNet50Conv5ROIFeatureExtractor(nn.Module):
    def __init__(self, config, in_channels):
        super(ResNet50Conv5ROIFeatureExtractor, self).__init__()

        resolution = config.MODEL.ROI_BOX_HEAD.POOLER_RESOLUTION
        scales = config.MODEL.ROI_BOX_HEAD.POOLER_SCALES
        sampling_ratio = config.MODEL.ROI_BOX_HEAD.POOLER_SAMPLING_RATIO
        pooler = Pooler( # 位于 modeling/pooler.py 文件中
            output_size=(resolution, resolution),
            scales=scales,
            sampling_ratio=sampling_ratio,
        )

        stage = resnet.StageSpec(index=4, block_count=3, return_features=False)
        head = resnet.ResNetHead(
            block_module=config.MODEL.RESNETS.TRANS_FUNC,
            stages=(stage,),
            num_groups=config.MODEL.RESNETS.NUM_GROUPS,
            width_per_group=config.MODEL.RESNETS.WIDTH_PER_GROUP,
            stride_in_1x1=config.MODEL.RESNETS.STRIDE_IN_1X1,
            stride_init=None,
            res2_out_channels=config.MODEL.RESNETS.RES2_OUT_CHANNELS,
            dilation=config.MODEL.RESNETS.RES5_DILATION
        )

        self.pooler = pooler
        self.head = head
        self.out_channels = head.out_channels

    def forward(self, x, proposals):
        x = self.pooler(x, proposals)
        x = self.head(x)
        return x

# 在注册器中进行注册
@registry.ROI_BOX_FEATURE_EXTRACTORS.register("FPN2MLPFeatureExtractor")
class FPN2MLPFeatureExtractor(nn.Module):
    """
    Heads for FPN for classification
    """

    def __init__(self, cfg, in_channels, half_out=False, cat_all_levels=False):
        super(FPN2MLPFeatureExtractor, self).__init__()
        # Proposals经过ROI Align之后得到size大小
        resolution = cfg.MODEL.ROI_BOX_HEAD.POOLER_RESOLUTION #7
        scales = cfg.MODEL.ROI_BOX_HEAD.POOLER_SCALES #(0.25, 0.125, 0.0625, 0.03125)
        sampling_ratio = cfg.MODEL.ROI_BOX_HEAD.POOLER_SAMPLING_RATIO #2
        # 进行ROI Align操作
        pooler = Pooler(
            output_size=(resolution, resolution),
            scales=scales,
            sampling_ratio=sampling_ratio,
            in_channels=in_channels,
            cat_all_levels=cat_all_levels,
        )
        # ROI Align之后得到的维度
        input_size = in_channels * resolution ** 2 #12544
        # 全连接层的输出维度
        representation_size = cfg.MODEL.ROI_BOX_HEAD.MLP_HEAD_DIM #4096
        use_gn = cfg.MODEL.ROI_BOX_HEAD.USE_GN #False
        # 定义ROI Align的类变量
        self.pooler = pooler
        # 定义全连接层的类变量
        self.fc6 = make_fc(input_size, representation_size, use_gn) #(12544,4096)

        if half_out:
            out_dim = int(representation_size / 2)
        else:
            out_dim = representation_size #4096
        
        self.fc7 = make_fc(representation_size, out_dim, use_gn) #(4096,4096)
        self.resize_channels = input_size #12544
        # 提取特征之后得到最终的输出维度
        self.out_channels = out_dim #4096

    # 进行提取特征操作
    def forward(self, x, proposals):
        # ROI Align操作
        x = self.pooler(x, proposals)
        # 进行展平 作为全连接层的输出
        x = x.view(x.size(0), -1)
        # 进行全连接层操作
        x = F.relu(self.fc6(x))
        x = F.relu(self.fc7(x))
        # 返回提取的特征
        return x

    def forward_without_pool(self, x):
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc6(x))
        x = F.relu(self.fc7(x))
        return x


@registry.ROI_BOX_FEATURE_EXTRACTORS.register("FPNXconv1fcFeatureExtractor")
class FPNXconv1fcFeatureExtractor(nn.Module):
    """
    Heads for FPN for classification
    """

    def __init__(self, cfg, in_channels):
        super(FPNXconv1fcFeatureExtractor, self).__init__()

        resolution = cfg.MODEL.ROI_BOX_HEAD.POOLER_RESOLUTION
        scales = cfg.MODEL.ROI_BOX_HEAD.POOLER_SCALES
        sampling_ratio = cfg.MODEL.ROI_BOX_HEAD.POOLER_SAMPLING_RATIO
        pooler = Pooler(
            output_size=(resolution, resolution),
            scales=scales,
            sampling_ratio=sampling_ratio,
        )
        self.pooler = pooler

        use_gn = cfg.MODEL.ROI_BOX_HEAD.USE_GN
        conv_head_dim = cfg.MODEL.ROI_BOX_HEAD.CONV_HEAD_DIM
        num_stacked_convs = cfg.MODEL.ROI_BOX_HEAD.NUM_STACKED_CONVS
        dilation = cfg.MODEL.ROI_BOX_HEAD.DILATION

        xconvs = []
        for ix in range(num_stacked_convs):
            xconvs.append(
                nn.Conv2d(
                    in_channels,
                    conv_head_dim,
                    kernel_size=3,
                    stride=1,
                    padding=dilation,
                    dilation=dilation,
                    bias=False if use_gn else True
                )
            )
            in_channels = conv_head_dim
            if use_gn:
                xconvs.append(group_norm(in_channels))
            xconvs.append(nn.ReLU(inplace=True))

        self.add_module("xconvs", nn.Sequential(*xconvs))
        for modules in [self.xconvs,]:
            for l in modules.modules():
                if isinstance(l, nn.Conv2d):
                    torch.nn.init.normal_(l.weight, std=0.01)
                    if not use_gn:
                        torch.nn.init.constant_(l.bias, 0)

        input_size = conv_head_dim * resolution ** 2
        representation_size = cfg.MODEL.ROI_BOX_HEAD.MLP_HEAD_DIM
        self.fc6 = make_fc(input_size, representation_size, use_gn=False)
        self.out_channels = representation_size

    # 进行提取特征操作
    def forward(self, x, proposals):
        # ROI Align操作
        x = self.pooler(x, proposals)
        x = self.xconvs(x)
        # 进行展平 作为全连接层的输出
        x = x.view(x.size(0), -1)
        # 进行全连接层操作
        x = F.relu(self.fc6(x))
        # 返回提取的特征
        return x


def make_roi_box_feature_extractor(cfg, in_channels, half_out=False, cat_all_levels=False):
    # 使用注册器获取该ROI_BOX_FEATURE_EXTRACTORS模块的对象
    # 对应的ROI_BOX_FEATURE_EXTRACTORS模块都定义在该函数上面
    func = registry.ROI_BOX_FEATURE_EXTRACTORS[
        cfg.MODEL.ROI_BOX_HEAD.FEATURE_EXTRACTOR #FPN2MLPFeatureExtractor
    ]
    return func(cfg, in_channels, half_out, cat_all_levels)