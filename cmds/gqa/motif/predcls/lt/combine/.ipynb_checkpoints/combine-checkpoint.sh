SG=/root/autodl-tmp/IETrans-SGG.pytorch
EXP=$SG/exps
OUTPATH=$EXP/50/motif/predcls/lt/combine/relabel
mkdir -p $OUTPATH
cd $OUTPATH
cp $SG/tools/ietrans/combine.py ./
python combine.py motif