python tools/internal_relabel.py --config-file "configs/wsup-GQA200.yaml"  \
  MODEL.ROI_RELATION_HEAD.USE_GT_BOX True \
  MODEL.ROI_RELATION_HEAD.USE_GT_OBJECT_LABEL True \
  MODEL.ROI_RELATION_HEAD.PREDICTOR TransformerPredictor \
  SOLVER.IMS_PER_BATCH 16 TEST.IMS_PER_BATCH 1 \
  DTYPE "float16" SOLVER.MAX_ITER 50000 \
  SOLVER.VAL_PERIOD 2000 \
  SOLVER.CHECKPOINT_PERIOD 2000 \
  GLOVE_DIR ../glove  \
  MODEL.PRETRAINED_DETECTOR_CKPT ../checkpoint/trans-precls-ori/model_0018000.pth \
  OUTPUT_DIR ./hlm  \
  SOLVER.PRE_VAL False \
  MODEL.ROI_RELATION_HEAD.PREDICT_USE_BIAS True \
  EM.MODE E
