#!/bin/bash

set -euo pipefail

JOBID="${1:?CRAB job ID is required}"

if ! [[ "${JOBID}" =~ ^[0-9]+$ ]]; then
    echo "ERROR: invalid CRAB job ID: ${JOBID}"
    exit 1
fi

NTHREADS=2

echo "CRAB Job ID : ${JOBID}"
echo "Threads     : ${NTHREADS}"
echo "CMSSW       : ${CMSSW_VERSION:-unset}"
echo "SCRAM_ARCH  : ${SCRAM_ARCH:-unset}"
echo "Host        : $(hostname)"
echo "PWD         : $(pwd)"

if [ "${CMSSW_VERSION:-}" != "CMSSW_15_0_2" ]; then
    echo "ERROR: expected CMSSW_15_0_2"
    exit 1
fi

echo " STEP 4/5 : MiniAOD"

cmsDriver.py \
    --python_filename MiniAOD_cfg.py \
    --eventcontent MINIAODSIM \
    --datatier MINIAODSIM \
    --filein file:input.root \
    --fileout file:MiniAOD.root \
    --conditions 150X_mcRun3_2024_realistic_v2 \
    --step PAT \
    --geometry DB:Extended \
    --era Run3_2024 \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    --mc \
    --nThreads "${NTHREADS}" \
    --no_exec \
    -n -1


cat > MiniAOD_runtime.py <<'EOF'
from MiniAOD_cfg import process
from PSet import process as crab_process

process.source.fileNames = (
    crab_process.source.fileNames
)

if hasattr(
    crab_process.source,
    "secondaryFileNames",
):
    process.source.secondaryFileNames = (
        crab_process.source.secondaryFileNames
    )


if hasattr(
    crab_process.source,
    "lumisToProcess",
):

    process.source.lumisToProcess = (
        crab_process.source.lumisToProcess
    )

process.maxEvents = (
    crab_process.maxEvents
)
EOF

echo
echo "+ cmsRun MiniAOD_runtime.py"
echo


cmsRun \
    -j MiniAOD_FrameworkJobReport.xml \
    MiniAOD_runtime.py

if [ ! -s MiniAOD.root ]; then
    echo "ERROR: MiniAOD.root was not produced"
    exit 1
fi

echo
echo "MiniAOD complete:"
ls -lh MiniAOD.root
echo

echo " STEP 5/5 : NanoAOD"

cmsDriver.py \
    --python_filename NanoAOD_cfg.py \
    --eventcontent NANOAODSIM \
    --datatier NANOAODSIM \
    --filein file:MiniAOD.root \
    --fileout file:NanoAOD.root \
    --conditions 150X_mcRun3_2024_realistic_v2 \
    --step NANO \
    --scenario pp \
    --geometry DB:Extended \
    --era Run3_2024 \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    --mc \
    --nThreads "${NTHREADS}" \
    --no_exec \
    -n -1


echo
echo "+ cmsRun NanoAOD_cfg.py"
echo

rm -f FrameworkJobReport.xml


# Final stage writes CRAB's actual FrameworkJobReport.
cmsRun \
    -j FrameworkJobReport.xml \
    NanoAOD_cfg.py

if [ ! -s NanoAOD.root ]; then
    echo "ERROR: NanoAOD.root was not produced"
    exit 1
fi

echo
echo "NanoAOD complete:"
ls -lh NanoAOD.root
echo
rm -f MiniAOD.root

echo " MiniAOD + NanoAOD SUCCESS"
echo "Final output:"
ls -lh NanoAOD.root
