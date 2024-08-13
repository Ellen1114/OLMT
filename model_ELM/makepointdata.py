#!/usr/bin/env python
import re, os, sys, csv, time, math
import numpy as np
from netCDF4 import Dataset
from geopy.distance import geodesic
from scipy.spatial import KDTree
import xarray as xr


#Function to return the indices of the nearest grid cell centers for a list of points
def get_pointindices_list(self, mylat, mylon, lat_grid, lon_grid, mask_grid=[]):
    #Ensure lon is -180 to 180 for both inputs
    mylon[mylon > 180] -= 360
    lon_grid[lon_grid > 180] -=360
    points = list(zip(lat_grid.flatten(),lon_grid.flatten()))
    #If mask given, only append land points
    if (len(mask_grid) == len(lat_grid)):
        maskf = mask_grid.flatten()
        for index, point in enumerate(points):
            if (maskf[index] == 0):
                points[index]=(-999,-999)
    original_shape = lat_grid.shape
    tree = KDTree(points)
    index_out = []
    for p in range(0,len(mylat)):
        target_point = (mylat[p], mylon[p])
        tree = KDTree(points)
        distance, index = tree.query(target_point)
        nearest_point = points[index]
        distance_km = geodesic(target_point, nearest_point).kilometers
        if (distance_km < 250):
            if (len(original_shape) > 1):
                # Convert the flattened index to a 2D index (row, column)
                row, col = np.unravel_index(index, original_shape)  
                index_out.append((row, col))
            else:
                index_out.append(index)
        else:
            print('Warning: Nearest gridcell to ',target_point)
            print(   'is ', distance_km, 'km away.  Not including')
    return index_out

def get_pointindices_bbox(self, lat_bounds, lon_bounds, lat_grid, lon_grid, mask_grid=[]):
    #Function to return all indices with a rectangular lat/lon bounding box
    # Ensure lon is within the range [-180, 180]
    lon_grid[lon_grid > 180] -= 360
    lon_bounds[lon_bounds > 180] -=360
    # Flatten the lat and lon grids to create a list of points
    points = list(zip(lat_grid.flatten(), lon_grid.flatten()))
    original_shape = lat_grid.shape
    index_out = []
    #If mask given, only append land points
    if (len(mask_grid) == len(lat_grid)):
        maskf = mask_grid.flatten()
    else:
        maskf = np.ones([len(points)],int)
    # Loop through all points in the grid and check if they fall within the bounding box
    for index, (lat, lon) in enumerate(points):
        if lat_bounds[0] <= lat <= lat_bounds[1] and lon_bounds[0] <= lon <= lon_bounds[1] \
                and maskf[index] > 0:
            if (len(original_shape) > 1):
                # Convert the flattened index to a 2D index (row, col)
                row, col = np.unravel_index(index, original_shape)
                index_out.append((row, col))
            else:
                index_out.append(index)
    return index_out


def subset_netcdf(self, index, input_file, output_file):
    # Load the input NetCDF file
    original_ds = xr.open_dataset(input_file, mode='r')
    subset_ds = xr.Dataset()

    # Select the variable and apply subsetting if specified
    for var_name, var_data in original_ds.data_vars.items():
        if ('lsmlat' in var_data.dims and 'lsmlon' in var_data.dims):
            #Extract from 2D surface data to 1D
            var_subset = var_data.isel(lsmlat=xr.DataArray([lat for lat, lon in index],dims='gridcell'), \
                 lsmlon=xr.DataArray([lon for lat, lon in index],dims='gridcell'))
        elif ('ni' in var_data.dims and 'nj' in var_data.dims):
            #Domain file
            var_subset = var_data.isel(nj=xr.DataArray([lat for lat, lon in index],dims='gridcell'), \
                 ni=xr.DataArray([lon for lat, lon in index],dims='gridcell'))
            var_subset = var_subset.expand_dims(dim={'dummy_dim': [1]})
            var_subset = var_subset.rename({'gridcell': 'ni', 'dummy_dim': 'nj'})
        elif ('gridcell' in var_data.dims):
            #Source dataset is 1D, simply extract
            var_subset = var_data.isel({gridcell: index})
        else:
            var_subset = var_data
        subset_ds[var_name] = var_subset

    # Save the new Dataset to the output file
    subset_ds.to_netcdf(output_file)
    subset_ds.close()
    original_ds.close()


def makepointdata(self, filename, mylat=[], mylon=[]):
    #Extract surface, domain, or pftdyn data from a given regional or global file.
    #If mylat and mylon are empty, it will use self.lat_bounds and self.lon_bounds to extract.

    mydata = Dataset(filename,'r')
    lonvar = 'LONGXY'
    latvar = 'LATIXY'
    #Figure out which type of file
    isdomain=False
    ispftdyn=False
    if ('domain' in filename):
        print('Creating domain data from ', filename)
        lonvar = 'xc'
        latvar = 'yc'
        infile  = self.domain_global
        outfile = self.OLMTdir+'/temp/domain.nc'
        #Save mask for other datasets
        self.mask_grid = mydata['mask'][:].copy()
        isdomain=True
    elif ('landuse' in filename or 'pftdyn' in filename):
        infile = self.pftdyn_global
        outfile = self.OLMTdir+'/temp/surfdata.pftdyn.nc'
        print('Creating land use data from ', filename)
        ispftdyn=True
    else:
        infile = self.surfdata_global
        outfile = self.OLMTdir+'/temp/surfdata.nc'
        print('Creating surface data from ', filename)
    
    #Get the site lat/lon
    if (self.site != ''):
        if (self.humhol):
            #If humhol, create two gridcells with same lat lon
            mylat = np.array([self.siteinfo['lat'], self.siteinfo['lat']])
            mylon = np.array([self.siteinfo['lon'], self.siteinfo['lon']])
        else:
            mylat = np.array([self.siteinfo['lat']])
            mylon = np.array([self.siteinfo['lon']])
        index = self.get_pointindices_list(mylat, mylon, mydata[latvar][:], mydata[lonvar][:], mask_grid=self.mask_grid) 
        self.subset_netcdf(index, infile,  outfile)
        if (not isdomain):
            ds = xr.open_dataset(outfile, mode='r+')
            #Set the site PFT and soil texture
            if (sum(self.siteinfo['PCT_NAT_PFT']) > 0):
                print('Setting PFT_NAT_PFT to: ', self.siteinfo['PCT_NAT_PFT'])
                #Assign PCT_NAT_PFT (should work whether 2, 3 or 4 dimensions)
                pct_nat_pft = xr.DataArray(self.siteinfo['PCT_NAT_PFT'], dims=['natpft'])
                ds['PCT_NAT_PFT'] = ds['PCT_NAT_PFT'] * 0 + pct_nat_pft.broadcast_like(ds['PCT_NAT_PFT'])
                #Assume we want to zero the other land units
                ds['PCT_NATVEG'][:] = 100.0
                print('Zeroing out other landunits')
                nonveg=['PCT_WETLAND','PCT_LAKE','PCT_URBAN','PCT_CROP','PCT_GLACIER']
                for v in nonveg:
                    ds[v][:] = 0.0
                if (not ispftdyn):
                    if (self.siteinfo['PCT_SAND'] >= 0):
                        ds['PCT_SAND'][:] = self.siteinfo['PCT_SAND']
                        print('Setting %SAND to ',self.siteinfo['PCT_SAND'])
                    if (self.siteinfo['PCT_CLAY'] >= 0):
                        ds['PCT_CLAY'][:] = self.siteinfo['PCT_CLAY']
                        print('Setting $CLAY to ',self.siteinfo['PCT_CLAY'])
                #else:  TODO - handle transitions
            ds.to_netcdf(outfile+'.tmp')
            ds.close()
            os.system('mv '+outfile+'.tmp '+outfile)
    #elif (self.point_list != ''):
