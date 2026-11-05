#!/usr/bin/env python3

# Copyright (c) 2026, Arm Limited or its affiliates. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Derive M3_SB_1 from its supporting SBMR requirements."""

import argparse
from pathlib import Path

from robot.api import ExecutionResult


PARENT_TAG = "M3_SB_1_PMCI_Side_Band_Interface_Declaration"

DEPENDENCIES = {
    "M3_SB_2": "M3_SB_2_PLDM_Platform_Functions",
    "M3_SB_3": "M3_SB_3_MCTP_Transport_Protocol",
    "M3_SB_4": "M3_SB_4_PLDM_Over_MCTP_Binding",
}


def collect_tests(suite):
    """Recursively collect tests from all Robot suites."""
    for test in suite.tests:
        yield test

    for child_suite in suite.suites:
        yield from collect_tests(child_suite)


def find_tests_by_tag(tests, tag):
    """Return all tests matching the specified tag."""
    return [
        test for test in tests
        if tag in test.tags
    ]


def derive_status(statuses):
    """Determine M3_SB_1 status from required child results."""
    child_statuses = [
        statuses.get(rule, "NOT_RUN")
        for rule in DEPENDENCIES
    ]

    if any(status == "FAIL" for status in child_statuses):
        return "FAIL"

    if all(status == "PASS" for status in child_statuses):
        return "PASS"

    return "SKIP"


def update_m3_sb_1(output_file):
    """Update the M3_SB_1 result in Robot Framework output."""

    result = ExecutionResult(str(output_file))
    tests = list(collect_tests(result.suite))

    # Find the M3_SB_1 parent test.
    parent_matches = find_tests_by_tag(tests, PARENT_TAG)

    if len(parent_matches) != 1:
        raise ValueError(
            "Expected exactly one M3_SB_1 parent test, "
            f"found {len(parent_matches)}"
        )

    parent = parent_matches[0]

    # Collect results from supporting requirements.
    statuses = {}

    for rule, tag in DEPENDENCIES.items():
        matches = find_tests_by_tag(tests, tag)

        if len(matches) == 0:
            statuses[rule] = "NOT_RUN"

        elif len(matches) == 1:
            statuses[rule] = matches[0].status

        else:
            raise ValueError(
                f"Multiple tests found for {rule}: {tag}"
            )

    # Derive M3_SB_1 from the child results.
    parent_status = derive_status(statuses)

    details = ", ".join(
        f"{rule}={status}"
        for rule, status in statuses.items()
    )

    # Update the parent test result.
    parent.status = parent_status
    parent.message = (
        "M3_SB_1 derived from supporting requirements: "
        + details
    )

    # Save the updated Robot Framework output.
    result.save(str(output_file))

    print(f"M3_SB_1: {parent_status}")
    print(details)


def main():
    parser = argparse.ArgumentParser(
        description="Derive M3_SB_1 from M3_SB_2, M3_SB_3 and M3_SB_4."
    )

    parser.add_argument(
        "output",
        help="Path to Robot Framework output.xml"
    )

    args = parser.parse_args()
    output_file = Path(args.output)

    if not output_file.is_file():
        parser.error(f"File not found: {output_file}")

    try:
        update_m3_sb_1(output_file)
    except (ValueError, OSError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
