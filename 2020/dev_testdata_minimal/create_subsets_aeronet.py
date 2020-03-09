#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Goal
"""

import numpy as np
from functools import reduce
import pyaerocom as pya
from pathlib import Path
import shutil

OUTBASE = Path(pya.const._TESTDATADIR).joinpath('obsdata')
 
if not OUTBASE.exists():
    OUTBASE.mkdir()

MIN_NUM_VALID = 300

IDS = {'sun'    :   'AeronetSunV3Lev2.daily',
       'sda'    :   'AeronetSDAV3Lev2.daily',
       'inv'    :   'AeronetInvV3Lev2.daily'
}

NETWORKS = {
    
    'sun'   :   'od550aer',
    'sda'   :   'od550lt1aer',
    'inv'    :  'abs550aer'        
}

filters = [

    ('altitude', [3000, 10000], 2),
    ('altitude', [0, 1000], 10),
    ('region_id','OCN', 2)                 
    ]

revision_files = {}
if __name__ == '__main__':
    
    loaded = {}
    for name, varlist in NETWORKS.items():
        reader = pya.io.ReadUngridded()
        _data = reader.read(IDS[name], varlist)
        loaded[name] = _data
        r = reader.get_reader()
        revision_files[name] = Path(r.DATASET_PATH).joinpath(r.REVISION_FILE)
    
    use_stats = []
    
    for (attr, val, num) in filters:
        subsets = {}
        statnames = []
        
        for name, data in loaded.items():
            subset = data.apply_filters(**{attr:val})
            subsets[name] = subset
            statnames.append(subset.unique_station_names)
            
        #same_stats = np.intersect1d(*statnames)
        
        same_stats = reduce(np.intersect1d, statnames)
        print(same_stats)
        
        stats_ok = []
        if len(same_stats) < num:
            raise Exception
        for statname in same_stats:
            if len(stats_ok) == num:
                print('YEAH')
                break
            statok = True
            for name, subset in subsets.items():
                var = NETWORKS[name]
                try:
                    stat = subset.to_station_data(statname)
                except pya.exceptions.DataCoverageError:
                    break
                data = stat[var]
                numvalid = np.sum(~np.isnan(data))
                if not numvalid > MIN_NUM_VALID:
                    statok = False
                    break
            if statok:
                stats_ok.append(statname)
        if not len(stats_ok) == num:
            raise Exception
        
        use_stats.extend(stats_ok)
    
    files = {
        
        'sun' : [],
        'sda' : [],
        'inv' : []
    }
    
    for name, data in loaded.items():
        data_id = IDS[name]
        outdir = OUTBASE.joinpath(data_id)
        # make sure to remove old data
        if outdir.exists():
            print('REMOVING EXISTING DATA FOR {}'.format(data_id))
            shutil.rmtree(outdir)
        outdir.mkdir()
        
        renamed = outdir.joinpath('renamed')
        renamed.mkdir()
        
        for statname in use_stats:
            idx = data._find_station_indices(statname)
            
            if len(idx) != 1:
                raise Exception
            fname = Path(data.metadata[idx[0]]['filename'])
            if not fname.exists():
                raise Exception
            dest = renamed.joinpath(fname.name)
            shutil.copy(str(fname), dest)
            files[name].append(str(fname))
        
        shutil.copy(revision_files[name], outdir.joinpath('Revision.txt'))
            
    
            