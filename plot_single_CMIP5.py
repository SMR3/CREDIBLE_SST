#! /usr/bin/env python  
#############################################################################
#
# Program : plot_single_CMIP5.py
# Author  : Neil Massey
# Purpose : Plot a timeseries of the GMSST of a single reconstructed SST field
#           plus the HadISST mean
# Inputs  : run_type  : rcp4.5 | rc8.5 | histo
#           ref_start : year to start reference period, 1850->2005
#           ref_end   : year to end reference period, 1850->2005
#           year      : year to take warming at as an alternative to warm
# Notes   : all reference values are calculated from the historical run_type
#           CMIP5 ensemble members are only included if their historical run 
#           includes the reference period
#           requires Andrew Dawsons eofs python libraries:
#            http://ajdawson.github.io/eofs/
# Output  : 
# Date    : 12/02/15
#
#############################################################################

import os, sys, getopt
from create_CMIP5_sst_anoms import get_concat_anom_sst_smooth_fname, get_concat_anom_sst_ens_mean_smooth_fname, get_start_end_periods
from create_HadISST_sst_anoms import get_HadISST_reference_fname, get_HadISST_smooth_fname, get_HadISST_residuals_fname, get_HadISST_monthly_residuals_fname, get_HadISST_annual_cycle_residuals_fname
from calc_CMIP5_EOFs import *
from cmip5_functions import calc_GMSST, load_data, reconstruct_field, load_sst_data
from filter_cmip5_members import read_cmip5_index_file
from create_HadISST_CMIP5_syn_SSTs import get_syn_sst_filename
from create_HadISST_sst_anoms import get_HadISST_reference_fname

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from netcdf_file import *
import numpy

#############################################################################

def plot_likely_range(sp, ref_start, ref_end, run_n):
    # plot the AR5 fig 11.25 likely range
    # first calc in GMT
    Y0 = 2009.0
    Y1 = 2025.5

    grad0 = (0.3-0.16)/(Y1 - Y0)
    grad1 = (0.7-0.16)/(Y1 - Y0)

    gmt_min0 = grad0*(2016-Y0) + 0.16
    gmt_max0 = grad1*(2016-Y0) + 0.16
    gmt_min1 = grad0*(2035-Y0) + 0.16
    gmt_max1 = grad1*(2035-Y0) + 0.16

    # convert to gmsst using the values of slope and intercept computed
    # by regressing the tos anomaly onto tas anomaly in CMIP5 ensemble members
    
    slope = 0.669
    intercept = 0.017
    
    # get the reference value
    histo_sy, histo_ey, rcp_sy, rcp_ey = get_start_end_periods()
    hadisst_ey = 2010
    hadisst_ref_fname = get_HadISST_reference_fname(histo_sy, hadisst_ey, ref_start, ref_end, run_n)
    hadisst_ref_sst = load_sst_data(hadisst_ref_fname, "sst")
    ref_gmsst = calc_GMSST(hadisst_ref_sst) -273.15
    
    gmsst_min0 = gmt_min0 * slope + intercept + ref_gmsst
    gmsst_max0 = gmt_max0 * slope + intercept + ref_gmsst
    gmsst_min1 = gmt_min1 * slope + intercept + ref_gmsst
    gmsst_max1 = gmt_max1 * slope + intercept + ref_gmsst

    l = sp.plot([2016,2035,2035,2016,2016],[gmsst_max0,gmsst_max1,gmsst_min1,gmsst_min0,gmsst_max0], 'k', lw=2.0)
    sp.plot([2016,2035], [(gmsst_max0+gmsst_min0)*0.5, (gmsst_max1+gmsst_min1)*0.5], 'k', lw=2.0)
    return l

#############################################################################

def plot_syn_GMSST(sp, run_type, ref_start, ref_end, neofs, eof_year, varmode, sample=50):
    # create the time axis
    histo_sy, histo_ey, rcp_sy, rcp_ey = get_start_end_periods()
    if varmode == 2:
        t_var = numpy.arange(histo_sy, rcp_ey+1, 1.0/12)
    else:
        t_var = numpy.arange(histo_sy, rcp_ey+1)

    # create the storage so that we can create an envelope of min / max values
    fname = get_syn_sst_filename(run_type, ref_start, ref_end, neofs, eof_year, sample, varmode)
    sst_data = load_sst_data(fname, "sst")
    gmsst_vals = calc_GMSST(sst_data) - 273.15
    l = sp.plot(t_var, gmsst_vals, 'r', lw=1.5, alpha=1.0, zorder=1)
    
    return l
    
#############################################################################

def plot_HadISST2(sp, resids=False, run_n="mm"):
    histo_sy, histo_ey, rcp_sy, rcp_ey = get_start_end_periods()
    hadisst_fname = get_HadISST_smooth_fname(histo_sy, 2010, run_n)
    hadisst_data = load_sst_data(hadisst_fname, "sst")
    if resids:
        hadisst_resids_fname = get_HadISST_residuals_fname(histo_sy, 2010, run_n)
        hadisst_resids = load_sst_data(hadisst_resids_fname, 'sst')
    else:
        hadisst_resids = 0
    t_var = numpy.arange(histo_sy, histo_sy+hadisst_data.shape[0])
    gmsst = calc_GMSST(hadisst_data+hadisst_resids) - 273.15
    l = sp.plot(t_var, gmsst, 'c', lw=1.5, alpha=1.0, zorder=2)
    return l

#############################################################################

if __name__ == "__main__":
    ref_start = -1
    ref_end = -1
    run_type = ""
    neofs = 0
    eof_year = 2050
    varintmode = 0
    runn = "mm"
    opts, args = getopt.getopt(sys.argv[1:], 'r:s:e:n:f:i:a:m:',
                               ['run_type=', 'ref_start=', 'ref_end=', 'neofs=', 'eof_year=',
                                'varint=', 'sample=', 'runn='])

    for opt, val in opts:
        if opt in ['--run_type', '-r']:
            run_type = val
        if opt in ['--ref_start', '-s']:
            ref_start = int(val)
        if opt in ['--ref_end', '-e']:
            ref_end = int(val)
        if opt in ['--neofs', '-n']:
            neofs = int(val)
        if opt in ['--eof_year', '-f']:
            eof_year = int(val)
        if opt in ['--varint', '-i']:
            varintmode = int(val)
        if opt in ['--sample', '-a']:
            sample = int(val)
        if opt in ['--runn', '-m']:
            runn = int(val)

    if varintmode == 0:
        varmodestring = "varnone"
    elif varintmode == 1:
        varmodestring = "varyear"
    elif varintmode == 2:
        varmodestring = "varmon"
    
    sp0 = plt.subplot(111)
    l_synth = plot_syn_GMSST(sp0, run_type, ref_start, ref_end, neofs, eof_year, varintmode, sample)
    l_hadisst = plot_HadISST2(sp0)
    l_likely = plot_likely_range(sp0, ref_start, ref_end, runn)
    sp0.legend([l_synth[0], l_hadisst[0]], ["Synthetic", "HadISST2", "AR5 likely"], loc=0)

    x0 = 1899
    x1 = 2100
    sp0.set_xlim([x0,x1])
    sp0.set_ylabel("GMSST $^\circ$C")
    sp0.set_xlabel("Year")

    f = plt.gcf()
    f.set_size_inches(8.0, 4.0)
    out_name = "cmip5_"+run_type+"_"+str(ref_start)+"_"+str(ref_end)+"_"+varmodestring+"_recon_a"+str(sample)+".pdf"

    plt.savefig(out_name)
