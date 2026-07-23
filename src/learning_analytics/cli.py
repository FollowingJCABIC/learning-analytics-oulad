from __future__ import annotations

import argparse
import json
import logging

from learning_analytics.analysis import build_analysis, build_model_plots
from learning_analytics.audit import build_source_audit
from learning_analytics.config import get_settings
from learning_analytics.dashboard import build_dashboard
from learning_analytics.download import download_dataset
from learning_analytics.modeling import train_models
from learning_analytics.reporting import build_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OULAD learning analytics workflow")
    parser.add_argument(
        "command",
        choices=["download", "audit", "analyze", "model", "report", "dashboard"],
        help="Workflow stage to run",
    )
    parser.add_argument("--force", action="store_true", help="Redownload the source archive")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args()
    settings = get_settings()
    if args.command == "download":
        print(download_dataset(settings, force=args.force))
    elif args.command == "audit":
        print(json.dumps(build_source_audit(settings)["calculated_scale"], indent=2))
    elif args.command == "model":
        print(train_models(settings).to_string(index=False))
        build_model_plots(settings)
    elif args.command == "analyze":
        build_analysis(settings)
    elif args.command == "report":
        print(build_report(settings))
    elif args.command == "dashboard":
        build_dashboard(settings)
