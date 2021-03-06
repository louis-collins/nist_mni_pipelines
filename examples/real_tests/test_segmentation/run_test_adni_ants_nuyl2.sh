#! /bin/sh


PREFIX=$(pwd)/../../python

export PYTHONPATH=$PREFIX:$PYTHONPATH

PARALLEL=4
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1

PYTHON=python

cat - > library_description.json <<END
{
  "reference_model": "adni_ec_bbox/model_t1w.mnc",
  "reference_mask":  "adni_ec_bbox/model_t1w.mnc",
  
  "reference_local_model" : null,
  "reference_local_mask" :  null,
  "library":"ec_library_bbox.csv",

  "build_remap":         [  [18 ,1],  
                            [1  ,2],   
                            [240,3], 
                            [16 ,4],  
                            [21 ,5],  
                            [19 ,6],  
                            [6  ,7],   
                            [47 ,8],  
                            [74 ,9],  
                            [87 ,10] ],
                            
  "build_flip_remap":    [  [3,  1],
                            [199,2],
                            [245,3],
                            [20, 4],
                            [4,  5],
                            [241,6],
                            [248,7],
                            [90, 8],
                            [5,  9],
                            [91, 10]  
                            ],
  "classes": 11,
  "build_symmetric": true,
  "build_symmetric_flip": true,
  "symmetric_lut": null,
  
  "initial_register": false,
  "initial_local_register": false,
  
  "non_linear_register": true,
  "non_linear_register_ants": true,
  
  "resample_order": 2,
  "resample_baa": true,
  "extend_boundary": 4,
  "op_mask": "E[2] D[4]",
  
  "create_patch_norm_lib": false,
  "patch_norm_lib_pct": 0.1,
  "patch_norm_lib_patch": 2,
  
  "pre_filters": {
    "normalize": true,
    "nuyl2":true
  }
  
}
END


if [ ! -e test_lib_nl2/library.json ];then
# create the library

${PYTHON} -m scoop -n $PARALLEL $PREFIX/iplScoopFusionSegmentation.py  \
  --create library_description.json --output test_lib_nl2 --debug
fi
# run cross-validation

cat - > cv.json <<END
{
  "validation_library":"ec_library_bbox.csv",
  "iterations":-1,
  "cv":1,
  "fuse_variant":"fuse_beta_none",
  "cv_variant":"cv_beta_none",
  "regularize_variant":"reg_1"
}
END


cat - > segment.json <<END
{
  "initial_local_register": false,
  "non_linear_pairwise": false,
  "non_linear_register": true,
  "non_linear_register_ants": true,

  "simple_fusion": false,
  "non_linear_register_level": 4,
  "pairwise_level": 4,

  "resample_order": 2,
  "resample_baa": true,
  "library_preselect": 3,
  "segment_symmetric": true,

  "fuse_options":
  {
      "patch": 1,
      "search": 1,
      "threshold": 0.0,
      "gco_diagonal": false,
      "gco_wlabel": 0.001,
      "gco":false,
      "beta":null,
      "new": false
  },
  "pre_filters": {
    "normalize": true,
    "nuyl2":true
  }
}
END

mkdir -p test_cv_nl

export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1
${PYTHON} -m scoop -n $PARALLEL -vvv \
  $PREFIX/iplScoopFusionSegmentation.py \
   --output test_cv_nl2 \
   --debug  \
   --segment test_lib_nl2 \
   --cv cv.json \
   --options segment.json 
