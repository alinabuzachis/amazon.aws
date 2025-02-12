#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: devopsguru_insight_info
short_description: Fetches information about DevOps Guru insights
version_added: 9.2.0
description:
    - Fetches information about DevOps Guru insights.
options:
    status_filter:
        description:
            - A dict of filters to apply.
            - You can specify which insights are returned by their start time and status ( ONGOING, CLOSED, or ANY).
            - See U(https://docs.aws.amazon.com/devops-guru/latest/APIReference/API_ListInsightsStatusFilter.html).
        type: dict
        aliases: ["filter"]
    account_id:
        description:
            - The ID of the Amazon Web Services account.
        type: str
    insight_id:
        description:
            - The ID of the insight.
        type: str
    include_anomalies:
        description:
            - The ID of the insight.
        type: dict
        suboptions:
            start_time_range:
                description:
                    - The ID of the insight.
                type: dict
                suboptions:
                    from_time:
                        description:
                            - The ID of the insight.
                        type: str
                    to_time:
                        description:
                            - The ID of the insight.
                        type: str
            filters:
                description:
                    - Specifies one or more service names that are used to list anomalies.
                type: dict
                suboptions:
                    service_collection:
                        description:
                            - A collection of the names of Amazon Web Services services.
                        type: dict
                        suboptions:
                            service_names:
                                description:
                                    - An array of strings that each specifies the name of an Amazon Web Services service.
                                type: list
                                elements: str
                                choices:
                                    - "API_GATEWAY"
                                    - "APPLICATION_ELB"
                                    - "AUTO_SCALING_GROUP"
                                    - "CLOUD_FRONT"
                                    - "DYNAMO_DB"
                                    - "EC2"
                                    - "ECS"
                                    - "EKS"
                                    - "ELASTIC_BEANSTALK"
                                    - "ELASTI_CACHE"
                                    - "ELB"
                                    - "ES"
                                    - "KINESIS"
                                    - "LAMBDA"
                                    - "NAT_GATEWAY"
                                    - "NETWORK_ELB"
                                    - "RDS"
                                    - "REDSHIFT"
                                    - "ROUTE_53"
                                    - "S3"
                                    - "SAGE_MAKER"
                                    - "SNS"
                                    - "SQS"
                                    - "STEP_FUNCTIONS"
                                    - "SWF"
    include_recommendations:
        description:
            - Dictionary for getting insight's recommendations.
        type: dict
        suboptions:
            locale:
                description:
                    - A locale that specifies the language to use for recommendations.
                type: str
                choices:
                    - 'DE_DE'
                    - 'EN_US'
                    - 'EN_GB'
                    - 'ES_ES'
                    - 'FR_FR'
                    - 'IT_IT'
                    - 'JA_JP'
                    - 'KO_KR'
                    - 'PT_BR'
                    - 'ZH_CN'
                    - 'ZH_TW'
                default: "EN_US"

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


from typing import Dict, Any, List, Union

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


@AWSRetry.jittered_backoff(retries=10)
def _fetch_data(client, api_call: str, **params: Dict[str, Any]) -> Dict[str, Any]:
    """Generic function to fetch data using paginators."""
    paginator = client.get_paginator(api_call)
    return paginator.paginate(**params).build_full_result()


def describe_insight(client, insight_id: str, account_id: str = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {"Id": insight_id}
    if account_id:
        params["AccountId"] = account_id

    return client.describe_insight(**params)


def get_insight_type(data: Dict[str, Any]) -> Union[str, None]:
    possible_keys = ["ProactiveInsight", "ReactiveveInsight", "ProactiveInsights", "ReactiveveInsights"]
    try:
        key = next(key for key in possible_keys if key in data)
        return key
    except StopIteration:
        return None


def merge_data(target: Union[Dict[str, Any], List[Dict[str, Any]]], source: Dict[str, Any]) -> None:
    """Merges data into a dictionary or list of dictionaries."""
    if isinstance(target, dict):
        target.update(source)
    elif isinstance(target, list):
        for item in target:
            item.update(source)


# @AWSRetry.jittered_backoff(retries=10)
# def _list_insights(client, **params) -> Dict[str, Any]:
#     paginator = client.get_paginator('list_insights')
#     return paginator.paginate(**params).build_full_result()


# @AWSRetry.jittered_backoff(retries=10)
# def _list_anomalies_for_insight(client, **params) -> Dict[str, Any]:
#     paginator = client.get_paginator('list_anomalies_for_insight')
#     return paginator.paginate(**params).build_full_result()


# @AWSRetry.jittered_backoff(retries=10)
# def _list_recommendations(client, **params) -> Dict[str, Any]:
#     paginator = client.get_paginator('list_recommendations')
#     return paginator.paginate(**params).build_full_result()


def main() -> None:
    argument_spec = dict(
        status_filter=dict(type="dict"),
        account_id=dict(type="str"),
        insight_id=dict(type="str"),
        include_anomalies=dict(type="dict"),
        include_recommendations=dict(type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        client = module.client("devops-guru", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    status_filter = module.params.get("status_filter")
    account_id = module.params.get("account_id")
    insight_id = module.params.get("insight_id")
    include_anomalies = module.params.get("include_anomalies")
    include_recommendations = module.params.get("include_recommendations")

    try:
        insight_info = describe_insight(client, insight_id, account_id) if insight_id else _fetch_data(client, "list_insights", StatusFilter=status_filter)

        insight_type = get_insight_type(insight_info)

        if insight_type:
            data_to_fetch = {
                "anomalies": (include_anomalies, "_fetch_data", "list_anomalies_for_insight"),
                "recommendations": (include_recommendations, "_fetch_data", "list_recommendations"),
            }

            for data_type, (include_flag, fetch_func, api_call) in data_to_fetch.items():
                if include_flag:
                    params = {}
                    if account_id:
                        params["AccountId"] = account_id

                    if data_type == "anomalies":
                        if include_flag.get("filters"):
                            params["Filters"] = include_flag["filters"]
                        if include_flag.get("start_time_range"):
                            params["StartTimeRange"] = include_flag["start_time_range"]

                    if data_type == "recommendations":
                        params["Locale"] = include_flag["locale"]

                    if isinstance(insight_info[insight_type], dict):
                        params["InsightId"] = insight_info[insight_type]["Id"]
                        fetched_data = globals()[fetch_func](client, api_call, **params)
                        merge_data(insight_info[insight_type], fetched_data)
                    elif isinstance(insight_info[insight_type], list):
                        for insight in insight_info[insight_type]:
                            params["InsightId"] = insight["Id"]
                            fetched_data = globals()[fetch_func](client, api_call, **params)
                            merge_data(insight, fetched_data)

            module.exit_json(**camel_dict_to_snake_dict(insight_info))

    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
