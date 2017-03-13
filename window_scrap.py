# -*- coding: utf-8 -*-
"""
Created on Thu Mar 02 16:31:16 2017

@author: Rdebbout
"""

import os
import itertools
import numpy as np
import rasterio as rs
import geopandas as gpd
from affine import Affine
from rasterio.crs import CRS
from rasterio import features
from shapely.geometry import Point
##############################################################################
os.getcwd()

lakes = gpd.read_file('./ohSevenA.shp')
fdr = rs.open("./fdr")
if fdr.crs != lakes.crs:
    lakes.to_crs({'init': u'epsg:5070'}, inplace=True)
meta = fdr.meta.copy()
meta.update(compress='lzw',
            nodata=0,
            dtype=rs.uint32,
            driver='GTiff',
            crs=CRS({'init': u'epsg:5070'}))
with rs.open("./lakes.tif" ,'w', **meta) as lksRas:
    lksArray = lksRas.read(1)
    shapes = ((g,v) for g,v in zip(lakes.geometry,lakes.COMID))
    burned = features.rasterize(shapes=shapes, fill=0,
                                out=lksArray,
                                out_shape=lksArray.shape,
                                transform=lksRas.transform)
    lksRas.write(burned.astype(rs.uint32), indexes=1)
##############################################################################
# something to look into...      
with rs.open("./fdr") as src:
    with rs.open("./lakes.tif", 'w', **src.profile) as dst:
        for _, window in src.aggregated_windows(reads=16):
            dst.write(src.read(window=window), window=window)  
##############################################################################
               
def makeAffine(tf, lbl, w, h):
    if lbl == 'A':
        return tf
    if lbl == 'B':
        return tf * tf.translation((w/2),0)
    if lbl == 'C':
        return tf * tf.translation(0,(h/2))
    if lbl == 'D':
        return tf * tf.translation((w/2),(h/2))
        

count = 0  
lksRas =  rs.open("./lakes.tif", 'w', **meta)
for win in wins:
    print("Making window {}.".format(win))
    arr = lksRas.read(1,window=win)
    shapes = ((g,v) for g,v in zip(lakes.geometry,lakes.COMID))
    burned = features.rasterize(shapes=shapes, fill=0,
                                out=arr,
                                out_shape=arr.shape,
                                transform=makeAffine(lksRas.transform,
                                                     count,
                                                     meta['width'],
                                                     meta['height']))
    if count == 0:
        keep = burned[0].copy()
    if count > 0:
        keep = np.column_stack((keep,burned[0].copy()))
    count += 1 
    lksRas.write(burned,window=win,indexes=1)    
# write out 1 window , change height/width/Affine 
# and make 4 separate writes
src = rs.open('./fdr')
meta = src.meta.copy()
w, h = src.width, src.height
meta.update(compress='lzw',
            nodata=0,
            dtype=rs.uint32,
            driver='GTiff',
            height = h/2,
            width = w/2,
            crs=CRS({'init': u'epsg:5070'}))

col_chunks = [(0, w/2), (w/2, w)]
row_chunks = [(0, h/2), (h/2, h)]

count = 0
for win, lbl in zip(itertools.product(row_chunks, col_chunks),['A','B','C','D']):
#    if count == 1:
#        break
#    count += 1
    #i, j = win
    meta.update(transform=makeAffine(src.transform,
                                 lbl,
                                 w,
                                 h))
    lksRas = rs.open("./lakes_%s.tif" % lbl, 'w', **meta)

    print lbl
    print meta['transform'][2]
    print meta['transform'][5]
    arr = lksRas.read(1)
    shapes = ((g,v) for g,v in zip(lakes.geometry,lakes.COMID))
    burned = features.rasterize(shapes=shapes, fill=0,
                                out=arr,
                                out_shape=arr.shape,
                                transform=makeAffine(src.transform,
                                                     lbl,
                                                     w,
                                                     h))    
    lksRas.write(burned,indexes=1)
lksRas = None
##############################################################################
    

for i, j in itertools.product(row_chunks, col_chunks):
    arr = src.read(1, window=(i, j))
    print i, j
    print arr.shape
    
for win, lbl in zip(itertools.product(row_chunks, col_chunks),['A','B','C','D']):
    print lbl
    print makeAffine(src.transform,lbl, w, h)
    print '*******************'
    
    meta.update(transform=makeAffine(src.transform,
                                     lbl, w, h))
    x = meta['transform'][2]
    y = meta['transform'][5]
    print x, y
    rt = gpd.GeoDataFrame({'Point':47},
                            geometry=[Point((x,y))],
                            crs={'init': u'epsg:5070'},index=[47])
    rt.to_file('./affPts/midPoint_%s.shp' % lbl)
    
578264.999999999883585,1914495.000
rt = gpd.GeoDataFrame({'Point':47},
                        geometry=[Point((x,y))],
                        crs={'init': u'epsg:5070'},index=[47])
rt.to_file('./affPts/midPoint_%s.shp' % lbl)
##############################################################################
h=np.array([1,2,3])
j=np.array([4,5,6])   
np.stack((h,j))    
np.vstack((h,j))
np.hstack((h,j))
np.dstack((h,j))
np.column_stack((h,j))  # this one!!!


#for win in wins:
#    print win
#    for x in win[0]:
#        if x != None:
#            print x * 30
#    for y in win[1]:
#        if y != None:
#            print y * 30
#            
#count = 0
#wins = fourViews(meta['width'],meta['height'])
#for win in wins:
#    print win
#    print makeAffine(lksRas.transform,count,meta['width'],meta['height'])
#    count += 1

# with every window the Affine neeeds to be changed..

# Affine(30.0, 0.0, 241514.99999999988,
#        0.0, -30.0, 2314035.0)

# 1 do nothing
# 2 subtract from last element
# 3 add to 3rd element
# 4 do both 2 & 3



## get zero point of a projection...in this case 5070
#from shapely.geometry import Point
#pt = gpd.GeoDataFrame({'Point':47},geometry=[Point((0,0))],crs={'init': u'epsg:5070'},index=[47])
#pt.to_file('{}/zeroPoint5070.shp'.format(out))
#
#rt = gpd.GeoDataFrame({'Point':47},geometry=[Point((241515,1914495))],crs={'init': u'epsg:5070'},index=[47])
#rt.to_file('{}/midPoint5070.shp'.format(out))


##############################################################################



##############################################################################

