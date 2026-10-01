from pathlib import Path

from CRABClient.UserUtilities import config

HERE = Path(__file__).resolve().parent


def make_config():
    cfg = config()
    cfg.General.workArea = str(HERE / "crab_projects")
    cfg.General.transferOutputs = True
    cfg.General.transferLogs = False
    cfg.General.instance = "prod"
    cfg.JobType.pluginName = "Analysis"
    cfg.JobType.psetName = str(HERE / "bookkeeping_cfg.py")
    cfg.JobType.scriptExe = str(HERE / "run_MiniNano.sh")
    cfg.JobType.numCores = 2
    cfg.JobType.maxMemoryMB = 4000
    cfg.JobType.maxJobRuntimeMin = 30
    cfg.Data.ignoreLocality = True
    cfg.Site.whitelist = ["T2_*"]
    cfg.Data.splitting = "FileBased"
    cfg.Data.ignoreLocality = True
    cfg.Data.publication = True
    cfg.Data.outputDatasetTag = "Private_Run3Summer24_NanoAOD"
    return cfg
