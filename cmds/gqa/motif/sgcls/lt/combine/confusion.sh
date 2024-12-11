python tools/internal_sg_relabel.py --config-file "configs/wsup-50.yaml"  \
  DATASETS.TRAIN \(\"50DS_VG_VGKB_train\",\) \
  MODEL.ROI_RELATION_HEAD.USE_GT_BOX True \
  MODEL.ROI_RELATION_HEAD.USE_GT_OBJECT_LABEL False \
  MODEL.ROI_RELATION_HEAD.PREDICTOR MotifPredictor \
  SOLVER.IMS_PER_BATCH 1 \
  TEST.IMS_PER_BATCH 1 \
  DTYPE "float16" SOLVER.MAX_ITER 100000 \
  SOLVER.VAL_PERIOD 2000 \
  SOLVER.CHECKPOINT_PERIOD 2000 \
  GLOVE_DIR ../glove \
  MODEL.PRETRAINED_DETECTOR_CKPT ../checkpoint/motif-sgcls-1.0/model_0010000.pth \
  OUTPUT_DIR ../checkpoint/motif-sgcls-1.0/  \
  MODEL.ROI_RELATION_HEAD.NUM_CLASSES 51 \
  SOLVER.PRE_VAL False \
  MODEL.ROI_RELATION_HEAD.PREDICT_USE_BIAS True \
  WSUPERVISE.DATASET InTransDataset  \
  EM.MODE SGE  \
  WSUPERVISE.SPECIFIED_DATA_FILE  em_E.pk_all_1.0 \
  Confusion_Name em_confusion.pk