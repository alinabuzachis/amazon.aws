#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: backup_plan
version_added: 6.0.0
short_description: create, delete and modify AWS Backup plans
description:
  - Manage AWS Backup plans.
  - For more information see the AWS documentation for Backup plans U(https://docs.aws.amazon.com/aws-backup/latest/devguide/about-backup-plans.html).
author:
  - Kristof Imre Szabo (@krisek)
  - Alina Buzachis (@alinabuzachis)
options:
  backup_plan_name:
    description:
      - The display name of a backup plan. Must contain 1 to 50 alphanumeric or '-_.' characters.
    required: true
    type: str
    aliases: ['name']
  rules:
    description:
      - An array of BackupRule objects, each of which specifies a scheduled task that is used to back up a selection of resources.
    required: false
    type: list
  advanced_backup_settings:
    description:
      -  Specifies a list of BackupOptions for each resource type. These settings are only available for Windows Volume Shadow Copy Service (VSS) backup jobs.
    required: false
    type: list
  state:
    description:
      - Create, delete a backup plan.
    required: false
    default: present
    choices: ['present', 'absent']
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags
"""

EXAMPLES = r"""
- name: create backup plan
  amazon.aws.backup_plan:
    state: present
    backup_plan_name: elastic
    rules:
      - RuleName: every_morning
        TargetBackupVaultName: elastic
        ScheduleExpression: "cron(0 5 ? * * *)"
        StartWindowMinutes: 120
        CompletionWindowMinutes: 10080
        Lifecycle:
          DeleteAfterDays: 7
        EnableContinuousBackup: true

"""
RETURN = r"""
backup_plan_arn:
    description: ARN of the backup plan.
    type: str
    sample: arn:aws:backup:eu-central-1:111122223333:backup-plan:1111f877-1ecf-4d79-9718-a861cd09df3b
backup_plan_id:
    description: Id of the backup plan.
    type: str
    sample: 1111f877-1ecf-4d79-9718-a861cd09df3b
backup_plan_name:
    description: Name of the backup plan.
    type: str
    sample: elastic
creation_date:
    description: Creation date of the backup plan.
    type: str
    sample: '2023-01-24T10:08:03.193000+01:00'
last_execution_date:
    description: Last execution date of the backup plan.
    type: str
    sample: '2023-03-24T06:30:08.250000+01:00'
tags:
    description: Tags of the backup plan
    type: str
version_id:
    description: Version id of the backup plan
    type: str
backup_plan:
    description: backup plan details
    returned: always
    type: complex
    contains:
        backup_plan_arn:
            description: backup plan arn
            returned: always
            type: str
            sample: arn:aws:backup:eu-central-1:111122223333:backup-plan:1111f877-1ecf-4d79-9718-a861cd09df3b
    backup_plan_name:
        description: backup plan name
        returned: always
        type: str
        sample:  elastic
    advanced_backup_settings:
        description: Advanced backup settings of the backup plan
        type: list
        elements: dict
        contains:
            resource_type:
                description: Resource type of the advanced setting
                type: str
            backup_options:
                description: Options of the advanced setting
                type: dict
    rules:
        description:
        - An array of BackupRule objects, each of which specifies a scheduled task that is used to back up a selection of resources.
        type: list

"""


try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule

import json
from typing import Optional
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.backup import get_plan_details


def create_backup_plan(module: AnsibleAWSModule, client, params: dict):
    """
    Creates a Backup Plan

    module : AnsibleAWSModule object
    client : boto3 backup client connection object
    params : The parameters to create a backup plan
    """
    params = {k: v for k, v in params.items() if v is not None}
    try:
        response = client.create_backup_plan(**params)
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to create Backup Plan")

    return response


def plan_update_needed(client, backup_plan_id: str, backup_plan_data: dict) -> bool:
    update_needed = False

    # we need to get current rules to manage the plan
    full_plan = client.get_backup_plan(BackupPlanId=backup_plan_id)

    configured_rules = json.dumps(
        [
            {key: val for key, val in rule.items() if key != "RuleId"}
            for rule in full_plan.get("BackupPlan", {}).get("Rules", [])
        ],
        sort_keys=True,
    )
    supplied_rules = json.dumps(backup_plan_data["BackupPlan"]["Rules"], sort_keys=True)

    if configured_rules != supplied_rules:
        # rules to be updated
        update_needed = True

    configured_advanced_backup_settings = json.dumps(
        full_plan.get("BackupPlan", {}).get("AdvancedBackupSettings", None),
        sort_keys=True,
    )
    supplied_advanced_backup_settings = json.dumps(
        backup_plan_data["BackupPlan"]["AdvancedBackupSettings"], sort_keys=True
    )
    if configured_advanced_backup_settings != supplied_advanced_backup_settings:
        # advanced settings to be updated
        update_needed = True
    return update_needed


def update_backup_plan(
    module: AnsibleAWSModule, client, backup_plan_id: str, backup_plan_data: dict
):
    try:
        response = client.update_backup_plan(
            BackupPlanId=backup_plan_id,
            BackupPlan=backup_plan_data["BackupPlan"],
        )
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to create Backup Plan")
    return response


def delete_backup_plan(module: AnsibleAWSModule, client, backup_plan_id: str):
    """
    Delete a Backup Plan

    module : AnsibleAWSModule object
    client : boto3 client connection object
    backup_plan_id : Backup Plan ID
    """
    try:
        client.delete_backup_plan(BackupPlanId=backup_plan_id)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to delete the Backup Plan")


def main():
    argument_spec = dict(
        state=dict(default="present", choices=["present", "absent"]),
        backup_plan_name=dict(required=True, type="str"),
        rules=dict(type="list"),
        advanced_backup_settings=dict(default=[], type="list"),
        creator_request_id=dict(type="str"),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
    )

    required_if = [
        ("state", "present", ["backup_plan_name", "rules"]),
        ("state", "absent", ["backup_plan_name"]),
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if, supports_check_mode=True)

    # collect parameters
    state = module.params.get("state")
    backup_plan_name = module.params["backup_plan_name"]
    purge_tags = module.params["purge_tags"]
    try:
        client = module.client("backup", retry_decorator=AWSRetry.jittered_backoff())
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    results = {"changed": False, "exists": False}

    current_plan = get_plan_details(module, client, backup_plan_name)

    if state == "present":
        new_plan_data = {
            "BackupPlan": {
                "BackupPlanName": backup_plan_name,
                "Rules": module.params["rules"],
                "AdvancedBackupSettings": module.params.get("advanced_backup_settings"),
            },
            "BackupPlanTags": module.params.get("tags"),
            "CreatorRequestId": module.params.get("creator_request_id"),
        }

        if not current_plan:  # Plan does not exist, create it
            results["exists"] = True
            results["changed"] = True

            if module.check_mode:
                module.exit_json(**results, msg="Would have created backup plan if not in check mode")

            create_backup_plan(module, client, new_plan_data)

            # TODO: add tags
            # ensure_tags(
            #     client,
            #     module,
            #     response["BackupPlanArn"],
            #     purge_tags=module.params.get("purge_tags"),
            #     tags=module.params.get("tags"),
            #     resource_type="BackupPlan",
            # )

        else:  # Plan exists, update if needed
            results["exists"] = True
            current_plan_id = current_plan[0]["backup_plan_id"]
            if plan_update_needed(client, current_plan_id, new_plan_data):
                results["changed"] = True

                if module.check_mode:
                    module.exit_json(**results, msg="Would have updated backup plan if not in check mode")

                update_backup_plan(module, client, current_plan_id, new_plan_data)

            if purge_tags:
                pass
                # TODO: Update plan tags
                # ensure_tags(
                #     client,
                #     module,
                #     response["BackupPlanArn"],
                #     purge_tags=module.params.get("purge_tags"),
                #     tags=module.params.get("tags"),
                #     resource_type="BackupPlan",
                # )

        new_plan = get_plan_details(module, client, backup_plan_name)
        results = results | new_plan[0]

    elif state == "absent":
        if not current_plan:  # Plan does not exist, can't delete it
            module.exit_json(**results)
        else:  # Plan exists, delete it
            results["changed"] = True

            if module.check_mode:
                module.exit_json(**results, msg="Would have deleted backup plan if not in check mode")

            delete_backup_plan(module, client, current_plan[0]["backup_plan_id"])

    module.exit_json(**results)


if __name__ == "__main__":
    main()