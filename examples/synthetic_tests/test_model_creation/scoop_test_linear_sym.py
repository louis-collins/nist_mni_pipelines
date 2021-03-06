from scoop import futures, shared

import iplScoopGenerateModel as gm

if __name__ == '__main__':
  # setup data for parallel processing
  
  j0=futures.submit( gm.generate_linear_model_csv,'subjects.lst',
    work_prefix='tmp_lsq6_sym',
    options={'symmetric':True, 'reg_type':'-lsq6', 'objective':'-xcorr', 'iterations':4,'refine':True, 'cleanup':True },
    model='test_data/ellipse_1.mnc',
    mask='test_data/mask.mnc')
    
  j1=futures.submit( gm.generate_linear_model_csv,'subjects.lst',
    work_prefix='tmp_lsq9_sym',
    options={'symmetric':True, 'reg_type':'-lsq9', 'objective':'-xcorr', 'iterations':4,'refine':True, 'cleanup':True },
    model='test_data/ellipse_1.mnc',
    mask='test_data/mask.mnc')

  j2=futures.submit( gm.generate_linear_model_csv,'subjects.lst',
    work_prefix='tmp_lsq12_sym',
    options={'symmetric':True, 'reg_type':'-lsq12', 'objective':'-xcorr', 'iterations':4,'refine':True, 'cleanup':True },
    model='test_data/ellipse_1.mnc',
    mask='test_data/mask.mnc')
  
  futures.wait([j0,j1,j2], return_when=futures.ALL_COMPLETED)
