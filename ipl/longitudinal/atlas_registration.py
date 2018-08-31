#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# @author Daniel
# @date 10/07/2011

version = '1.0'

#
# Atlas registration
#
from ipl.minc_tools import mincTools,mincError
from ipl.registration import non_linear_register_full
from ipl.ants_registration import  non_linear_register_ants2
from ipl.elastix_registration import  register_elastix
from .general import *



# Run preprocessing using patient info
# - Function to read info from the pipeline patient
# - pipeline_version is employed to select the correct version of the pipeline
def pipeline_atlasregistration(patient, tp=None):
    
    if os.path.exists(patient.nl_xfm):
        print(' -- pipeline_atlasregistration exists')
        return True
    return atlasregistration_v10(patient)


def atlasregistration_v10(patient):

    nl_level = 2

    if patient.fast:  # fast mode
        nl_level = 4

    with mincTools() as minc:
        model_t1   = patient.modeldir + os.sep + patient.modelname + '.mnc'
        model_mask = patient.modeldir + os.sep + patient.modelname + '_mask.mnc'

        if patient.nlreg=='ants':
            non_linear_register_ants2(
                patient.template['nl_template'],
                model_t1,
                patient.nl_xfm,
                source_mask=patient.template['nl_template_mask'],
                target_mask=model_mask,
                level=nl_level
                )
        elif patient.nlreg=='elastix':
            register_elastix(
                patient.template['nl_template'],
                model_t1,
                output_xfm=patient.nl_xfm,
                source_mask=patient.template['nl_template_mask'],
                target_mask=model_mask
                )
        else:
            non_linear_register_full(
                patient.template['nl_template'],
                model_t1,
                patient.nl_xfm,
                source_mask=patient.template['nl_template_mask'],
                target_mask=model_mask,
                level=nl_level,
                )
        
        # make QC image, similar to linear ones
        if not os.path.exists(patient.qc_jpg['nl_template_nl']):
            atlas_outline = patient.modeldir + os.sep + patient.modelname + '_outline.mnc'
            minc.resample_smooth(patient.template['nl_template'],minc.tmp('nl_atlas.mnc'),transform=patient.nl_xfm)
            minc.qc(
                minc.tmp('nl_atlas.mnc'),
                patient.qc_jpg['nl_template_nl'],
                title=patient.id,
                image_range=[0, 120],
                big=True,
                clamp=True,
                mask=atlas_outline
                )

# kate: space-indent on; indent-width 4; indent-mode python;replace-tabs on;word-wrap-column 80;show-tabs on
