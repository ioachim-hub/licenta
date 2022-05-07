#!/usr/bin/env python3

from typing import Optional
from abc import ABCMeta, abstractmethod
import enum
import json
import subprocess
import os
import argparse
import pathlib
import dataclasses

import pydantic


class Build(pydantic.BaseModel):
    context: str = "./"
    dockerfile: str


class Entry(pydantic.BaseModel):
    """
    Files referenced by Config must contain a list of these entries
    Example entry which we need to build:
    {
      "name": "grafana-init",
      "tag": ["1.0.0"],
      "force": true,
      "build": {
        "dockerfile": "docker/grafana-init/Dockerfile",
        "context": "docker/grafana-init"
      }
    }

    Example entry which we just need to rename:
    {
        "repo": "k8s.gcr.io",
        "name": "kube-state-metrics/kube-state-metrics",
        "tag": ["v2.1.1"]
    }
    """

    # where is this image located. For images that we build, this field will be empty
    repo: Optional[str]
    #
    name: str
    tag: list[str]
    force: bool = False
    build: Optional[Build] = None


class ZstdConfig(pydantic.BaseModel):
    # zstd level
    level: int
    # zstd -T: 0 means Multi threading
    threads: int


class Backend(str, enum.Enum):
    DOCKER = "docker"
    PODMAN = "podman"


class Environment(str, enum.Enum):
    GENERIC = "generic"
    AWS = "aws"


class SkopeoConfig(pydantic.BaseModel):
    dest_compress_format: Optional[str] = "gzip"
    dest_compress_level: int = 9
    debug: bool = False
    format: str = "oci"
    retries: int = 2


class AWSConfig(pydantic.BaseModel):
    region: str


class Config(pydantic.BaseModel):
    """
    Main config file which references a list of files
    """

    repo_url: str
    backend: Backend
    pull_skip_if_exists: bool
    push: bool
    pusher: str = "backend"  # "skopeo"

    save: bool
    save_dir: str = "/tmp"
    save_force: bool = False

    environment: Environment
    aws: Optional[AWSConfig] = None
    zstd_config: ZstdConfig = ZstdConfig(level=7, threads=0)
    skopeo_config: SkopeoConfig = SkopeoConfig()
    files: list[pydantic.FilePath]


class Instruction(metaclass=ABCMeta):
    @abstractmethod
    def to_shellcmd(self) -> str:
        raise RuntimeError("unimplemented")


@dataclasses.dataclass
class GenericInstruction(Instruction):
    cmd: str

    def to_shellcmd(self) -> str:
        return self.cmd


@dataclasses.dataclass
class AwsCreateRepoInstruction(Instruction):
    region: str
    name: str

    def to_shellcmd(self) -> str:
        cmd = "aws "
        cmd += f"--region {self.region}"
        cmd += " ecr create-repository"
        cmd += " --image-scanning-configuration scanOnPush=false"
        cmd += f" --repository-name {self.name}"

        cmd = f"{cmd} || true"

        return cmd


@dataclasses.dataclass
class PullInstruction(Instruction):
    # backend that will execute the command
    backend: Backend
    # final container image name: repo/name:tag
    repo: str
    name: str
    tag: str
    skip_if_exists: bool

    def to_shellcmd(self) -> str:
        src_uri = f"{self.repo}/{self.name}:{self.tag}"
        cmd = f"{self.backend} pull {src_uri}"

        if self.skip_if_exists:
            cmd = f"if ! {self.backend} inspect {src_uri} &> /dev/null; then {cmd}; fi"

        return cmd


@dataclasses.dataclass
class BuildInstruction(Instruction):
    backend: Backend
    name: str
    tag: str
    dockerfile_path: str
    context_path: str

    def to_shellcmd(self) -> str:
        uri = f"{self.name}:{self.tag}"

        if self.backend == Backend.PODMAN:
            cmd = (
                f"{self.backend} build --disable-compression=false "
                + "-f {self.dockerfile_path} -t {uri} {self.context_path}"
            )
        elif self.backend == Backend.DOCKER:
            cmd = f"{self.backend} build -f {self.dockerfile_path} -t {uri} {self.context_path}"
        else:
            raise RuntimeError(f"Unsupported backend {self.backend}")

        return cmd


@dataclasses.dataclass
class SkopeoPushInstruction(Instruction):
    backend: Backend
    skopeo_cfg: SkopeoConfig
    src_repo: Optional[str]
    name: str
    tag: str
    dst_repo: str
    force: bool

    def to_shellcmd(self) -> str:
        if self.src_repo is None:
            self.src_repo = "localhost"

        cmd = "skopeo copy"
        if self.skopeo_cfg.debug:
            cmd += " --debug"

        cmd += f" --format {self.skopeo_cfg.format}"
        cmd += f" --retry-times {self.skopeo_cfg.retries}"
        if self.skopeo_cfg.dest_compress_format is not None:
            cmd += f" --dest-compress-format {self.skopeo_cfg.dest_compress_format}"
            cmd += f" --dest-compress-level {self.skopeo_cfg.dest_compress_level}"

        uri = f"{self.name}:{self.tag}"
        src_uri = f"containers-storage:{self.src_repo}/{uri}"
        dst_uri = f"docker://{self.dst_repo}/{uri}"
        cmd += f" {src_uri} {dst_uri}"

        if self.force is False:
            cmd = f"if ! skopeo inspect {dst_uri} &> /dev/null; then {cmd}; fi;"

        return cmd


@dataclasses.dataclass
class BackendPushInstruction(Instruction):
    backend: Backend
    src_repo: Optional[str]
    name: str
    tag: str
    dst_repo: str
    force: bool

    def to_shellcmd(self) -> str:
        uri = f"{self.name}:{self.tag}"
        if self.backend == Backend.PODMAN:
            src_repo = self.src_repo
            if src_repo is None:
                src_repo = "localhost"

            src_uri = f"containers-storage:{src_repo}/{uri}"
            dst_uri = f"docker://{self.dst_repo}/{uri}"

            cmd = f"podman push {src_uri} {dst_uri}"
        elif self.backend == Backend.DOCKER:
            if self.src_repo is None:
                src_uri = f"{uri}"
            else:
                src_uri = f"{self.src_repo}/{uri}"
            dst_uri = f"{self.dst_repo}/{uri}"

            cmd = f"docker tag {src_uri} {dst_uri} && docker push {dst_uri}"

        return cmd


@dataclasses.dataclass
class SaveInstruction(Instruction):
    backend: Backend
    dst_dir: str
    name: str
    tag: str
    force: bool
    zstd_config: ZstdConfig

    def zstd_cmd(self, output_path: str) -> str:
        zstd_cfg = self.zstd_config

        level = zstd_cfg.level
        threads = zstd_cfg.threads
        cmd = f"zstd -{level} -T{threads}"

        if self.force:
            cmd += " -f"

        cmd += f" -o {output_path}"

        return cmd

    def to_shellcmd(self) -> str:
        uri = f"{self.name}:{self.tag}"
        file_path = uri.replace("/", "_").replace(":", "__") + ".tar.zst"
        output_path = f"{self.dst_dir}/{file_path}"

        backend_cmd = f"{self.backend} save {uri}"
        compress_cmd = self.zstd_cmd(output_path=output_path)
        save_cmd = f"{backend_cmd} |{compress_cmd}"

        cmd = f"mkdir -p {self.dst_dir} && " + save_cmd

        return cmd


@dataclasses.dataclass
class EntryPlan:
    entry: Entry
    instructions: list[Instruction]


class Mgr:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.backend = cfg.backend
        self.entries: list[Entry] = []

    def load_from_file(self, file_path: pathlib.Path) -> None:
        with open(file_path, "rb") as fp:
            file_json = json.load(fp)
            file_entries = [Entry.parse_obj(x) for x in file_json]

            self.entries.extend(file_entries)

    def filter_on(self, name: str) -> None:
        filtered_entries = [x for x in self.entries if name in x.name]

        self.entries = filtered_entries

    def exec(self) -> None:
        plans = self.generate_entryplans()

        for plan in plans:
            self.exec_entryplan(plan)

    def exec_entryplan(self, x: EntryPlan) -> None:
        for instruction in x.instructions:
            cmd = instruction.to_shellcmd()
            print(f"[mgr] [DEBUG] running '{cmd}'")
            subprocess.run(cmd, shell=True, check=True)

    def generate_entryplans(self) -> list[EntryPlan]:
        ret: list[EntryPlan] = []

        for x in self.entries:
            plans = self.entry_to_entryplan(entry=x)

            ret.extend(plans)

        return ret

    def entry_to_entryplan(self, entry: Entry) -> list[EntryPlan]:
        backend = self.cfg.backend
        plans = []

        for tag in entry.tag:
            """
            Workflow:
            * Pull or build.
            * Push or save to a local file.
            """
            instructions: list[Instruction] = []

            if entry.repo:
                instructions.append(
                    PullInstruction(
                        backend=backend,
                        repo=entry.repo,
                        name=entry.name,
                        tag=tag,
                        skip_if_exists=self.cfg.pull_skip_if_exists,
                    )
                )
            elif entry.build is not None:
                instructions.append(
                    BuildInstruction(
                        backend=backend,
                        name=entry.name,
                        tag=tag,
                        dockerfile_path=entry.build.dockerfile,
                        context_path=entry.build.context,
                    )
                )
            else:
                raise RuntimeError("repo or build must be specified")

            if self.cfg.push:
                if self.cfg.environment == Environment.AWS:
                    assert self.cfg.aws is not None
                    aws_cfg = self.cfg.aws

                    instructions.append(
                        AwsCreateRepoInstruction(region=aws_cfg.region, name=entry.name)
                    )

                push_instr: Instruction
                if self.cfg.pusher == "skopeo":
                    push_instr = SkopeoPushInstruction(
                        backend=backend,
                        skopeo_cfg=self.cfg.skopeo_config,
                        src_repo=entry.repo,
                        name=entry.name,
                        tag=tag,
                        dst_repo=self.cfg.repo_url,
                        force=entry.force,
                    )
                elif self.cfg.pusher == "backend":
                    push_instr = BackendPushInstruction(
                        backend=backend,
                        src_repo=entry.repo,
                        name=entry.name,
                        tag=tag,
                        dst_repo=self.cfg.repo_url,
                        force=entry.force,
                    )
                else:
                    raise RuntimeError("unknown pusher")

                instructions.append(push_instr)

            if self.cfg.save:
                instructions.append(
                    SaveInstruction(
                        backend=backend,
                        dst_dir=self.cfg.save_dir,
                        name=entry.name,
                        tag=tag,
                        force=self.cfg.save_force,
                        zstd_config=self.cfg.zstd_config,
                    )
                )

            plans.append(EntryPlan(entry=entry, instructions=instructions))

        return plans


def main() -> None:
    """ """
    parser = argparse.ArgumentParser(
        add_help=True,
    )
    parser.add_argument(
        "--config", type=str, help="Config JSON file path", required=True, default=None
    )
    parser.add_argument(
        "--root_path", type=str, help="root path", required=True, default=None
    )
    parser.add_argument("--name_filter", type=str, required=False, default=None)
    parser.add_argument("--file_filter", type=str, required=False, default=None)
    parser.add_argument("--backend", type=Backend, required=False, default=None)
    args = parser.parse_args()

    print(f"config: {args.config}")
    print(f"root_path: {args.root_path}")
    os.chdir(args.root_path)

    with open(args.config, "rb") as fp:
        cfg = Config.parse_obj(json.load(fp))

    if args.backend is not None:
        cfg.backend = args.backend

    mgr = Mgr(cfg)
    for file_path in cfg.files:
        if args.file_filter:
            if args.file_filter not in str(file_path):
                continue

        mgr.load_from_file(file_path)

    if args.name_filter:
        mgr.filter_on(args.name_filter)

    mgr.exec()


if __name__ == "__main__":
    main()
