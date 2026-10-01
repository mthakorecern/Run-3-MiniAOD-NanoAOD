import FWCore.ParameterSet.Config as cms

process = cms.Process("BOOKKEEPING")
process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring("file:input.root"),
)
process.options = cms.untracked.PSet(
    numberOfThreads=cms.untracked.uint32(2),
    numberOfStreams=cms.untracked.uint32(0),
)
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))
process.NANOAODoutput = cms.OutputModule(
    "PoolOutputModule",
    fileName=cms.untracked.string("NanoAOD.root"),
    outputCommands=cms.untracked.vstring("keep *"),
    dataset=cms.untracked.PSet(
        dataTier=cms.untracked.string("NANOAODSIM"),
        filterName=cms.untracked.string(""),
    ),
)
process.NANOAODoutput_step = cms.EndPath(process.NANOAODoutput)
