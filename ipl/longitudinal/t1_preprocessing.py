#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# @author Daniel, Vladimir S. FONOV
# @date 10/07/2011

version = '1.0'

#
# Preprocessing functions
# - mri 2 tal
# - n3 correction
# - denoising
# - vol pol

from optparse import OptionParser  # to change when python updates in the machines for argparse
from optparse import OptionGroup  # to change when python updates in the machines for argparse

from ipl.minc_tools import mincTools,mincError

from .general import *
from .patient import *

import shutil

# Run preprocessing using patient info
# - Function to read info from the pipeline patient
# - pipeline_version is employed to select the correct version of the pipeline

def pipeline_t1preprocessing(patient, tp):

  # checking if processing was performed

    if os.path.exists(patient[tp].qc_jpg['stx_t1']) \
        and os.path.exists(patient[tp].clp['t1']) \
        and os.path.exists(patient[tp].stx_xfm['t1']) \
        and os.path.exists(patient[tp].stx_mnc['t1']) \
        and os.path.exists(patient[tp].stx_ns_xfm['t1']) \
        and os.path.exists(patient[tp].stx_ns_mnc['t1']):
        print(' -- pipeline_t1preprocessing was already performed')
    else:
        # # Run the appropiate version
        t1preprocessing_v10(patient, tp)

    # Writing QC images
    # #####################
    # qc stx registration

    modeloutline = patient.modeldir + os.sep + patient.modelname + '_outline.mnc'

    with mincTools(  ) as minc:
        minc.qc(
            patient[tp].stx_mnc['t1'],
            patient[tp].qc_jpg['stx_t1'],
            title=patient[tp].qc_title,
            image_range=[0, 120],
            mask=modeloutline,
            big=True,
            clamp=True,
            )
    return True


def t1preprocessing_v10(patient, tp):

    # # processing data
    # ##################
    with mincTools() as minc:
        tmpt1 =    minc.tmp('float_t1.mnc')
        tmpmask =  minc.tmp('mask_t1.mnc')
        tmpn3 =    minc.tmp('n3_t1.mnc')
        tmpstats = minc.tmp('volpol_t1.stats')
        tmpxfm =   minc.tmp('stx_t1.xfm')
        tmpnlm =   minc.tmp('nlm_t1.mnc')

        modelt1   = patient.modeldir + os.sep + patient.modelname + '.mnc'
        modelmask = patient.modeldir + os.sep + patient.modelname + '_mask.mnc'

        init_xfm = None
        if 'stx_t1' in patient[tp].manual \
            and os.path.exists(patient[tp].manual['stx_t1']):
            init_xfm = patient[tp].manual['stx_t1']

        # Manual clp t1
        if 'clp_t1' in patient[tp].manual \
            and os.path.exists(patient[tp].manual['clp_t1']):
                
            shutil.copyfile(patient[tp].manual['clp_t1'],  patient[tp].clp['t1'])
            tmpt1 = patient[tp].clp['t1']  # In order to make the registration if needed

        if not os.path.exists( patient[tp].clp['t1'] ):

            minc.reshape( patient[tp].native['t1'], tmpt1 )

            for s in ['xspace', 'yspace', 'zspace']:
                spacing = minc.query_attribute( tmpt1, s + ':spacing' )

                if spacing.count( 'irregular' ):
                    minc.set_attribute( tmpt1, s + ':spacing', 'regular__' )

            # 3. denoise
            if patient.denoise:
                minc.nlm( tmpt1, tmpnlm, beta=0.7 ) # TODO: maybe USE anlm sometimes?
            else:
                tmpnlm = tmpt1

            if     not os.path.exists( patient[tp].clp['t1'] ) \
                or not os.path.exists( patient[tp].nuc['t1']):

                if patient.n4:
                    minc.winsorize_intensity(tmpt1,minc.tmp('trunc_t1.mnc'))
                    minc.binary_morphology(minc.tmp('trunc_t1.mnc'),'',minc.tmp('otsu_t1.mnc'),binarize_bimodal=True)
                    minc.defrag(minc.tmp('otsu_t1.mnc'),minc.tmp('otsu_defrag_t1.mnc'))
                    minc.autocrop(minc.tmp('otsu_defrag_t1.mnc'),minc.tmp('otsu_defrag_expanded_t1.mnc'),isoexpand='50mm')
                    minc.binary_morphology(minc.tmp('otsu_defrag_expanded_t1.mnc'),'D[25] E[25]',minc.tmp('otsu_expanded_closed_t1.mnc'))
                    minc.resample_labels(minc.tmp('otsu_expanded_closed_t1.mnc'),minc.tmp('otsu_closed_t1.mnc'),like=minc.tmp('trunc_t1.mnc'))
                    
                    minc.calc([minc.tmp('trunc_t1.mnc'),minc.tmp('otsu_closed_t1.mnc')], 'A[0]*A[1]',  minc.tmp('trunc_masked_t1.mnc'))
                    minc.calc([tmpt1,minc.tmp('otsu_closed_t1.mnc')],'A[0]*A[1]' ,minc.tmp('masked_t1.mnc'))
                    
                    minc.linear_register( minc.tmp('trunc_masked_t1.mnc'), modelt1, tmpxfm,
                            init_xfm=init_xfm, 
                            objective='-nmi', conf=patient.linreg )
                    
                    minc.resample_labels( modelmask, minc.tmp('brainmask_t1.mnc'),
                            transform=tmpxfm, invert_transform=True,
                            like=minc.tmp('otsu_defrag_t1.mnc') )
                    
                    minc.calc([minc.tmp('otsu_defrag_t1.mnc'),minc.tmp('brainmask_t1.mnc')],'A[0]*A[1]',minc.tmp('weightmask_t1.mnc'))
                    
                    dist=200
                    if patient.mri3T: dist=50 # ??
                    
                    minc.n4(minc.tmp('masked_t1.mnc'),
                            output_field=patient[tp].nuc['t1'],
                            output_corr=tmpn3,
                            iter='200x200x200x200',
                            weight_mask=minc.tmp('weightmask_t1.mnc'),
                            mask=minc.tmp('otsu_closed_t1.mnc'),
                            distance=dist,
                            downsample_field=4,
                            datatype='short'
                            )
                    # shrink?
                    minc.volume_pol(
                        tmpn3,
                        modelt1,
                        patient[tp].clp['t1'],
                        source_mask=minc.tmp('weightmask_t1.mnc'),
                        target_mask=modelmask,
                        datatype='-short',
                        )
                elif patient.mask_n3:
                    # 2. Reformat mask
                    minc.linear_register( tmpt1, modelt1, tmpxfm,
                            init_xfm=init_xfm, 
                            objective='-nmi', 
                            conf=patient.linreg )

                    minc.resample_labels( modelmask, tmpmask,
                            transform=tmpxfm, invert_transform=True,
                            like=tmpnlm )

                    minc.nu_correct( tmpnlm, output_image=tmpn3,
                                     mask=tmpmask, 
                                     mri3t=patient.mri3T,
                                     output_field=patient[tp].nuc['t1'],
                                     downsample_field=4,
                                     datatype='short')

                    minc.volume_pol(
                        tmpn3,
                        modelt1,
                        patient[tp].clp['t1'],
                        source_mask=tmpmask,
                        target_mask=modelmask,
                        datatype='-short',
                        )
                else:
                    minc.nu_correct( tmpnlm, 
                                     output_image=tmpn3,
                                     mri3t=patient.mri3T,
                                     output_field=patient[tp].nuc['t1'],
                                     downsample_field=4,
                                     datatype='short')

                    minc.volume_pol( tmpn3, modelt1, patient[tp].clp['t1'], 
                                     datatype='-short' )
        # register to the stx space
        t1_corr = patient[tp].clp['t1']
        
        if 't1' in patient[tp].geo and patient.geo_corr:
            t1_corr = patient[tp].corr['t1'] #TODO: avoid double resampling for the output!
            minc.resample_smooth( patient[tp].clp['t1'],
                                  t1_corr,
                                  transform=patient[tp].geo['t1'] )

        if not os.path.exists( patient[tp].stx_xfm['t1']):
            minc.linear_register( t1_corr, modelt1,
                                  patient[tp].stx_xfm['t1'],
                                  init_xfm=init_xfm,
                                  objective='-nmi', 
                                  conf=patient.linreg)

                                  # target_mask=modelmask

        minc.resample_smooth( t1_corr,
                              patient[tp].stx_mnc['t1'], like=modelt1,
                              transform=patient[tp].stx_xfm['t1'] )

        # stx no scale
        minc.xfm_noscale( patient[tp].stx_xfm['t1'],
                          patient[tp].stx_ns_xfm['t1'])

        minc.resample_smooth(t1_corr,
                             patient[tp].stx_ns_mnc['t1'],
                             like=modelt1,
                             transform=patient[tp].stx_ns_xfm['t1'])



# kate: space-indent on; indent-width 4; indent-mode python;replace-tabs on;word-wrap-column 80;show-tabs on
