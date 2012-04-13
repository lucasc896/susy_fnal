#!/bin/sh
source /uscmst1/prod/sw/cms/cmsset_default.sh
source /uscms_data/d3/clucas/susy_test/SUSYv2/setup.sh
cd /uscms_data/d3/clucas/susy_test/SUSYv2/../CMSSW_5_0_0/src
cmsenv
cd /uscms_data/d3/clucas/susy_test/SUSYv2/chris_truth/python
./bMulti.py -j __susyJob__bMulti.py_20120413_09_20_42/job.json -J $1 -S __susyJob__bMulti.py_20120413_09_20_42/status/$1
