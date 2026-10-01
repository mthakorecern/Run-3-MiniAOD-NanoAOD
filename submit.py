#!/usr/bin/env python3

import argparse
import csv
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CMSSW_SRC = HERE.parent
BASE_DIR = CMSSW_SRC.parents[1]
DEFAULT_CSV = BASE_DIR / "campaign" / "campaign.csv"
CRAB_USERNAME = "mithakor"
INPUT_TAG = "Private_Run3Summer24_RECO"


def require_environment():
    if os.environ.get("CMSSW_VERSION") != "CMSSW_15_0_2":
        raise RuntimeError("Run cmsenv inside CMSSW_15_0_2 first.")
    if shutil.which("dasgoclient") is None:
        raise RuntimeError("Missing command: dasgoclient")
    try:
        import CRABAPI.RawCommand

    except ImportError as exc:
        raise RuntimeError(
            "CRAB API is unavailable. " "Run crab-setup.sh before submitting."
        ) from exc


def read_csv(path):
    rows = {}
    with Path(path).open() as handle:
        for row in csv.DictReader(handle):
            rows[int(row["Mass"])] = row
    if not rows:
        raise RuntimeError(f"No campaign entries found in {path}")
    return rows


def select_masses(
    rows,
    requested,
):
    if not requested:
        return sorted(rows)

    missing = [mass for mass in requested if mass not in rows]
    if missing:
        raise RuntimeError(
            "Masses missing from campaign CSV: "
            + ", ".join(
                map(
                    str,
                    missing,
                )
            )
        )
    return sorted(set(requested))


EXPECTED_RECO_FILES = 1000


def run_das(query):
    result = subprocess.run(
        [
            "dasgoclient",
            "--query",
            query,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        raise RuntimeError(f"DAS query failed:\n" f"{query}\n\n" f"{result.stderr}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def count_dataset_files(dataset):
    files = run_das(f"file dataset={dataset} " f"instance=prod/phys03")
    return len(set(files))


def find_reco_dataset(row):
    dataset_name = row["Dataset Name"].strip()
    pattern = f"/{dataset_name}/" f"{CRAB_USERNAME}-{INPUT_TAG}-*/USER"
    print()
    print("Searching for:")
    print(f"  {pattern}")
    datasets = sorted(
        set(run_das(f"dataset dataset={pattern} " f"instance=prod/phys03"))
    )
    if not datasets:
        raise RuntimeError(
            f"No published RECO dataset found for " f"M={row['Mass']}:\n" f"  {pattern}"
        )
    complete = []
    print()

    for dataset in datasets:
        nfiles = count_dataset_files(dataset)
        print(f"  {nfiles:4d} files : {dataset}")
        if nfiles == EXPECTED_RECO_FILES:
            complete.append(dataset)

    if len(complete) == 0:
        raise RuntimeError(
            f"No complete RECO dataset found for "
            f"M={row['Mass']}.\n"
            f"Expected exactly "
            f"{EXPECTED_RECO_FILES} files."
        )

    if len(complete) > 1:

        raise RuntimeError(
            f"More than one complete RECO dataset "
            f"was found for M={row['Mass']}:\n" + "\n".join(complete)
        )

    print(f"\nSelected complete RECO dataset " f"({EXPECTED_RECO_FILES} files):")
    print(f"  {complete[0]}")
    return complete[0]


def validate_reco_inputs(
    rows,
    masses,
):
    reco_datasets = {}

    print()
    print("Validating all published RECO inputs")

    failures = []

    for mass in masses:
        try:
            reco_dataset = find_reco_dataset(rows[mass])
            reco_datasets[mass] = reco_dataset
            print(f"M={mass}: OK")

        except Exception as exc:
            failures.append((mass, str(exc)))
            print()
            print(f"M={mass}: FAILED")
            print(str(exc))
    print()

    if failures:
        print(f"{len(failures)} mass point(s) " f"are not ready.")
        print()

        for mass, message in failures:

            print(f"M={mass}:")
            print(f"  {message}")

        raise RuntimeError(
            "RECO input validation failed. " "No MiniNano jobs were submitted."
        )

    print(
        f"All {len(masses)} RECO datasets "
        f"contain exactly "
        f"{EXPECTED_RECO_FILES} files."
    )

    return reco_datasets


def submit_mass(
    row,
    reco_dataset,
    units_per_job,
    out_lfn_dir_base,
    storage_site,
):
    from CRABAPI.RawCommand import crabCommand
    from crabConfig import make_config

    mass = int(row["Mass"])
    dataset_name = row["Dataset Name"]
    request_name = f"{row['CRAB Request Name']}_NanoAOD"
    cfg = make_config()

    cfg.General.requestName = request_name
    cfg.Data.inputDataset = reco_dataset
    cfg.Data.inputDBS = "phys03"
    cfg.Data.unitsPerJob = units_per_job
    cfg.Data.outLFNDirBase = out_lfn_dir_base
    cfg.Site.storageSite = storage_site

    print(f"Submitting MiniAOD+NanoAOD M={mass}")
    print(f"Request name : {request_name}")
    print(f"Input dataset:")
    print(f"  {reco_dataset}")
    print(f"Files/job    : {units_per_job}")
    print(f"Output LFN   : {out_lfn_dir_base}")
    print(f"Storage site : {storage_site}")
    print()
    crabCommand(
        "submit",
        config=cfg,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default=str(DEFAULT_CSV),
    )
    parser.add_argument(
        "--masses",
        nargs="+",
        type=int,
    )
    parser.add_argument(
        "--units-per-job",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--out-lfn-dir-base",
        required=True,
        help=("Example: " "/store/user/mithakor/" "SignalProduction/Run3Summer24"),
    )
    parser.add_argument(
        "--storage-site",
        default="T2_US_Wisconsin",
    )
    args = parser.parse_args()
    require_environment()
    if args.units_per_job != 1:
        raise RuntimeError("This production is configured for " "--units-per-job 1")
    rows = read_csv(args.csv)
    masses = select_masses(
        rows,
        args.masses,
    )
    reco_datasets = validate_reco_inputs(
        rows,
        masses,
    )
    for mass in masses:
        submit_mass(
            row=rows[mass],
            reco_dataset=reco_datasets[mass],
            units_per_job=args.units_per_job,
            out_lfn_dir_base=args.out_lfn_dir_base,
            storage_site=args.storage_site,
        )


if __name__ == "__main__":
    main()
