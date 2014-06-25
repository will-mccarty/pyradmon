#!/usr/bin/env python
# PyRadmon v1.0 - Python Radiance Monitoring Tool
# Copyright 2014 Albert Huang.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
# 
# Main Wrapper Library -
#   library for combining everything together!
# 

import sys

from core import *
import args
import config
import config_printer
from config import *

from enumerate import enumerate, enumerate_all
from data import get_data, get_data_columns, post_data_columns, SPECIAL_FIELDS
from plot import plot, subst_data

try:
    from prettytable import PrettyTable
except:
    print "ERROR: PrettyTable is needed to run this script!"

def main():
    parser = args.make_argparser()
    parse = parser.parse_args()
    (pyradmon_config, plot_dict, parse_data) = args.parse_to_config(parse)
    
    if not pyradmon_config:
        sys.exit(1)
    
    ###################################################################
    ## VERB ACTION CODE
    ###################################################################
    
    ## Config verb + Config args, part 2
    if parse.verb == "config":
        if isset_obj("config_display", parse) and parse.config_display:
            # Print configuration
            config_printer.display(pyradmon_config, plot_dict)
        if isset_obj("config_save", parse):
            # Print configuration
            config.save(parse.config_save, pyradmon_config, plot_dict)
        # That's it! Exit...
        sys.exit(0)
    
    # Everything else gets pretty involved!
    if parse.verb == "plot" or parse.verb == "dump" or parse.verb == "list":
        if parse.verb == "dump" or parse.verb == "list":
            enum_opts_dict = config.postprocess_config(pyradmon_config)
            if "data_columns" in enum_opts_dict:
                data_var_list = enum_opts_dict["data_columns"]
            else:
                data_var_list = []
        else:
            (enum_opts_dict, data_var_list) = config.postprocess(pyradmon_config, plot_dict)
            pprinter(enum_opts_dict)
        
        if "data_all" in pyradmon_config and pyradmon_config["data_all"]:
            info(" ** Enumerating ALL data files...")
            (en, stats) = enumerate_all(**enum_opts_dict)
        else:
            en = enumerate(**enum_opts_dict)
            (tmp_en, stats) = enumerate_all(**enum_opts_dict)
        
    pprinter(en)
    if parse.verb == "plot" or parse.verb == "dump":
        chans = enum_opts_dict["data_channels"]
        
        info(" ** Fetching data for channel %s..." % (chans[0] if len(chans) == 1 else \
                    " and ".join(chans) if len(chans) == 2 else \
                    (", ".join(chans[:-1]) + ", and " + chans[-1])))
        if parse.verb == "dump":
            tmp_columns = get_data_columns(en)
            columns = post_data_columns(tmp_columns)
            new_columns = []
            
            if "data_type" in enum_opts_dict:
                for prefix in enum_opts_dict['data_type'].split("|"):
                    for column in columns:
                        if column in SPECIAL_FIELDS:
                            if column not in new_columns:
                                new_columns.append(column)
                        else:
                            new_columns.append(prefix + "|" + column)
                columns = new_columns
            else:
                warn("No data type specified - will use ges by default.")
                for column in columns:
                    if column in SPECIAL_FIELDS:
                        new_columns.append(column)
                    else:
                        new_columns.append("ges|" + column)
            
            data_var_list = columns
            dat = get_data(en, data_var_list, gen_channel_list(chans))
        else:
            dat = get_data(en, data_var_list, gen_channel_list(chans))
    
    if parse.verb == "list":
        #pprinter(stats)
        start_date_str = "%s%s%s_%sz" % (str(stats["start_year"]).zfill(4), \
                                        str(stats["start_month"]).zfill(2), \
                                        str(stats["start_day"]).zfill(2), \
                                        str(stats["start_hour"]).zfill(2))
        end_date_str = "%s%s%s_%sz" % (str(stats["end_year"]).zfill(4), \
                                        str(stats["end_month"]).zfill(2), \
                                        str(stats["end_day"]).zfill(2), \
                                        str(stats["end_hour"]).zfill(2))
        maxlen = len("Files matching instrument/sat and data_type:") + 1
        
        outstrs = []
        
        outstr = "| " + "Data range:".ljust(maxlen) + "%s - %s" % (start_date_str, end_date_str)
        outstrs.append(outstr)
        
        outstr = "| " + "Average interval:".ljust(maxlen) + "%s hrs" % (str(stats["average_interval"]))
        outstrs.append(outstr)
        
        outstr = "| " + "Total files:".ljust(maxlen) + "%i files" % (stats["total_files"])
        outstrs.append(outstr)
        
        outstr = "| " + "Files matching instrument/sat and data_type:".ljust(maxlen) + "%i files" % (stats["criteria_total_files"])
        outstrs.append(outstr)
        
        outstr = "| " + "Available data types:".ljust(maxlen) + ", ".join(stats["available_data_type"])
        outstrs.append(outstr)
        
        outstr = "| " + "Available instrument/sats:".ljust(maxlen) + ", ".join(stats["available_instrument_sat"])
        outstrs.append(outstr)
        
        maxtotallen = max([len(x) for x in outstrs])
        outstrs_final = [ x.ljust(maxtotallen)+" |" for x in outstrs ]
        
        print "=" * (maxtotallen + 2)
        print "| Data Information".ljust(maxtotallen) + " |"
        print "=" * (maxtotallen + 2)
        
        for outstr in outstrs_final:
            print outstr
        
        print "=" * (maxtotallen + 2)
        
        sys.exit(0)
    
    if parse.verb == "dump":
        pprinter(dat)
        sys.exit(0)
    
    if parse.verb == "plot":
        for channel in gen_channel_list(chans):
            info(" ** Plotting data for channel %i..." % channel)
            
            enum_opts_dict["channel"] = channel
            
            try:
                plot_dict_subs = subst_data(plot_dict, dat[channel])
                plot(plot_dict_subs, dat[channel], enum_opts_dict)
                del plot_dict_subs
            except:
                critical("An error occurred! Error follows:")
                critical(traceback.format_exc())
                #print "Dumping data_dict:"
                #pprint.pprint(dat)
                critical("Exiting.")
                sys.exit(1)

if __name__ == "__main__":
    main()
