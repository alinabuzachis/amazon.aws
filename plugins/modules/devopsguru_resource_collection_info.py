#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: devopsguru_resource_collection_info
short_description: Fetches information about a DevOps Guru resource collection
version_added: 9.2.0
description:
    - Manages DevOps Guru resource collections.
options:
    resource_collection_type:
        description:
            - The type of Amazon Web Services resource collections to return.
            - The one valid value is V(CLOUD_FORMATION) for Amazon Web Services CloudFormation stacks.
        type: str
        required: True
        choices:
            - 'AWS_CLOUD_FORMATION'
            - 'AWS_SERVICE'
            - 'AWS_TAGS'
extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
author:
    - Alina Buzachis (@alinabuzachis)
"""

EXAMPLES = r"""

"""

RETURN = r"""

"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry



@AWSRetry.jittered_backoff(retries=10)
def _get_resource_collection(client, module):
    params = {"ResourceCollectionType": module.params.get("resource_collection_type")}
    try:
        paginator = client.get_paginator("get_resource_collection")
        return paginator.paginate(**params).build_full_result()["ResourceCollection"]
    except is_boto3_error_code("ResourceNotFoundException"):
        return {}


def main() -> None:
    argument_spec = dict(
        resource_collection_type=dict(required=True, type="str", choices=['AWS_CLOUD_FORMATION', 'AWS_SERVICE', 'AWS_TAGS']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[("cloudformation_stack_names", "tags")],
    )

    try:
        client = module.client("devops-guru", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")


    try:
        module.exit_json(**camel_dict_to_snake_dict(_get_resource_collection(client, module)))
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
