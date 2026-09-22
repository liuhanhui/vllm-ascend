#!/usr/bin/env python3
# Copyright (c) 2026 Huawei Technologies Co., Ltd. All Rights Reserved.
# This file is a part of the vllm-ascend project.
"""Upload a 310P experimental ops-transformer .run to Aliyun OSS.

Credentials must come from the environment. Do not put AccessKey material in
git, Dockerfiles, or chat logs.

Required:
  OSS_ACCESS_KEY_ID
  OSS_ACCESS_KEY_SECRET

Optional:
  OSS_ENDPOINT   default oss-cn-shanghai.aliyuncs.com
  OSS_BUCKET     default test-cann
  OSS_PREFIX     default CANN/temp_ops-transformer
  OSS_ACL        default public-read (needed for Dockerfile wget)

Install helper: pip install oss2
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is not set. Export it in the shell; do not commit secrets.")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_file", type=Path, help="Path to cann-ops-transformer_experimental_310p_linux-*.run")
    parser.add_argument(
        "--object-key",
        default="",
        help="OSS object key. Default: ${OSS_PREFIX}/<filename>",
    )
    args = parser.parse_args()

    run_file = args.run_file.expanduser().resolve()
    if not run_file.is_file():
        raise SystemExit(f"run file not found: {run_file}")

    try:
        import oss2
    except ImportError as exc:
        raise SystemExit("oss2 is required: pip install oss2") from exc

    access_key_id = _require_env("OSS_ACCESS_KEY_ID")
    access_key_secret = _require_env("OSS_ACCESS_KEY_SECRET")
    endpoint = os.environ.get("OSS_ENDPOINT", "oss-cn-shanghai.aliyuncs.com").strip()
    bucket_name = os.environ.get("OSS_BUCKET", "test-cann").strip()
    prefix = os.environ.get("OSS_PREFIX", "CANN/temp_ops-transformer").strip().strip("/")
    acl = os.environ.get("OSS_ACL", "public-read").strip()
    object_key = args.object_key.strip() or f"{prefix}/{run_file.name}"

    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    print(f"Uploading {run_file.name} -> oss://{bucket_name}/{object_key}")
    bucket.put_object_from_file(object_key, str(run_file))
    if acl:
        bucket.put_object_acl(object_key, acl)
    public_url = f"https://{bucket_name}.{endpoint}/{object_key}"
    print(f"Uploaded. Public wget URL (if ACL allows): {public_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
